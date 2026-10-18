import base64
import json

import httpx
import pytest

from solvecha import (
    AsyncSolvecha,
    InvalidKeyError,
    OutOfCreditError,
    Solvecha,
    SolveTimeoutError,
)
from solvecha.tools import functions, openai_tools

PNG = base64.b64encode(b"\x89PNG\r\n\x1a\nxxxx").decode()
KEY = "slv_" + "a" * 32


class FakeAPI:
    """Imitates the Solvecha API. ``polls_before`` answers are 'incomplete job'."""

    def __init__(self, polls_before=1, answer=None, create_error=None):
        self.requests = []
        self.polls = 0
        self.polls_before = polls_before
        self.answer = answer if answer is not None else [False, True, False, True, True, False, False, False, False]
        self.create_error = create_error

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        self.requests.append((request.method, request.url.path, request.url.query.decode(), body, request.headers.get("authorization")))
        if request.headers.get("authorization") != f"Bearer {KEY}":
            return httpx.Response(401, json={"error": 15, "message": "Invalid key"})
        if request.url.path == "/v1/status":
            return httpx.Response(200, json={"plan": "Free", "status": "Active", "credit": 99, "quota": 100, "balance_usd": "0.00", "ttl": 10})
        if request.url.path == "/v1/feedback":
            return httpx.Response(200, json={"data": "ok"})
        if request.method == "POST":
            if self.create_error:
                return httpx.Response(403, json={"error": self.create_error, "message": "x"})
            return httpx.Response(200, json={"data": "job-1"})
        self.polls += 1
        if self.polls <= self.polls_before:
            return httpx.Response(409, json={"error": 14, "message": "Incomplete job"})
        return httpx.Response(200, json={"data": self.answer})


def client(fake, **kw):
    return Solvecha(KEY, http=httpx.Client(transport=httpx.MockTransport(fake)), poll_interval=0, **kw)


def test_solve_recaptcha_returns_tiles_and_never_sends_the_key_in_the_body():
    fake = FakeAPI()
    result = client(fake).solve_recaptcha("Select all images with buses", "3x3", PNG)
    assert result.tiles == [2, 4, 5]
    assert result.positions == ["row 1, column 2", "row 2, column 1", "row 2, column 2"]
    method, path, _, body, auth = fake.requests[0]
    assert (method, path) == ("POST", "/v1/recognition/recaptcha")
    assert body == {"task": "Select all images with buses", "grid": "3x3", "image_data": [PNG]}
    assert "key" not in body and auth == f"Bearer {KEY}"
    assert fake.polls == 2


def test_file_path_and_data_url_and_bytes(tmp_path):
    path = tmp_path / "grid.png"
    path.write_bytes(base64.b64decode(PNG))
    for image in (str(path), path, base64.b64decode(PNG), "data:image/png;base64," + PNG):
        fake = FakeAPI(polls_before=0)
        client(fake).solve_recaptcha("t", "3x3", image)
        assert fake.requests[0][3]["image_data"] == [PNG]


def test_grid_validation_happens_before_any_request():
    fake = FakeAPI()
    with pytest.raises(ValueError):
        client(fake).solve_recaptcha("t", "5x5", PNG)
    with pytest.raises(ValueError):
        client(fake).solve_recaptcha("t", "3x3", [PNG, PNG])
    assert fake.requests == []


def test_other_types():
    c = client(FakeAPI(polls_before=0, answer=["x7k2p"]))
    assert c.solve_text(PNG).text == "x7k2p"
    assert client(FakeAPI(polls_before=0, answer={"x": 42.5})).solve_geetest([PNG, PNG]).offset_percent == 42.5
    fake = FakeAPI(polls_before=0, answer=[True, False, False, False, False, False])
    assert client(fake).solve_funcaptcha("Pick the sheep", PNG, match=True).tiles == [1]
    assert fake.requests[0][1] == "/v1/recognition/funcaptcha_match"


def test_errors_map_to_exceptions():
    with pytest.raises(OutOfCreditError):
        client(FakeAPI(create_error=16)).solve_recaptcha("t", "3x3", PNG)
    bad = Solvecha("slv_wrong", http=httpx.Client(transport=httpx.MockTransport(FakeAPI())), poll_interval=0)
    with pytest.raises(InvalidKeyError):
        bad.status()


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("SOLVECHA_API_KEY", raising=False)
    with pytest.raises(InvalidKeyError):
        Solvecha()


def test_timeout_reports_the_job_id():
    with pytest.raises(SolveTimeoutError) as info:
        client(FakeAPI(polls_before=10**6)).solve("recaptcha", {}, timeout=0.05)
    assert info.value.job_id == "job-1"


def test_report_and_status():
    fake = FakeAPI()
    c = client(fake)
    assert c.status()["plan"] == "Free"
    assert c.report_result("job-1", "accepted", "3x3")
    assert fake.requests[-1][3] == {"job_id": "job-1", "verdict": "accepted", "grid": "3x3"}


async def test_async_client():
    fake = FakeAPI()
    c = AsyncSolvecha(KEY, http=httpx.AsyncClient(transport=httpx.MockTransport(fake)), poll_interval=0)
    assert (await c.solve_recaptcha("t", "3x3", PNG)).tiles == [2, 4, 5]
    assert (await c.status())["credit"] == 99


def test_tool_functions_never_raise():
    funcs = functions(client(FakeAPI(create_error=16)))
    out = funcs["solve_recaptcha_grid"]("t", "3x3", PNG)
    assert "Out of credit" in out["error"]
    assert "grid must be" in funcs["solve_recaptcha_grid"]("t", "9x9", PNG)["error"]


def test_openai_tools_dispatch():
    tools, handle = openai_tools(client(FakeAPI()))
    assert {t["function"]["name"] for t in tools} == {"solve_recaptcha_grid", "solve_text_captcha", "get_account_status", "report_result"}
    out = json.loads(handle("solve_recaptcha_grid", json.dumps({"task": "t", "grid": "3x3", "image": PNG})))
    assert out["selected_tiles"] == [2, 4, 5]
    assert "unknown tool" in json.loads(handle("nope", "{}"))["error"]
    assert "bad arguments" in json.loads(handle("solve_text_captcha", "{}"))["error"]
    assert "not valid JSON" in json.loads(handle("get_account_status", "{oops"))["error"]
