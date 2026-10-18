from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional, Sequence, Union

import httpx

from . import core
from .core import Image
from .errors import SolveTimeoutError, error_for
from .results import GeetestResult, GridResult, TextResult

DEFAULT_TIMEOUT = 45.0
POLL_INTERVAL = 1.0


def _body(response: httpx.Response) -> Dict[str, Any]:
    try:
        parsed = response.json()
    except ValueError:
        return {"error": 9, "message": f"HTTP {response.status_code}"}
    return parsed if isinstance(parsed, dict) else {"data": parsed}


class Solvecha:
    """Synchronous client. ``api_key`` defaults to the SOLVECHA_API_KEY environment variable."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = core.DEFAULT_BASE_URL,
        http: Optional[httpx.Client] = None,
        poll_interval: float = POLL_INTERVAL,
    ):
        self._key = core.resolve_key(api_key)
        self._poll = poll_interval
        self._http = http or httpx.Client(timeout=30)
        self._base = base_url.rstrip("/")

    def _request(self, method: str, path: str, json: Any = None) -> Dict[str, Any]:
        response = self._http.request(method, self._base + path, json=json, headers=core.headers(self._key))
        return _body(response)

    def solve(self, kind: str, payload: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT) -> tuple:
        """Create a job and wait for the answer. Returns (job_id, data)."""
        job_id = core.job_id_from(self._request("POST", f"/v1/recognition/{kind}", payload))
        deadline = time.monotonic() + timeout
        while True:
            time.sleep(self._poll)
            answer = self._request("GET", f"/v1/recognition/{kind}?id={job_id}")
            code = core.error_code(answer)
            if code == 0 and "data" in answer:
                return job_id, answer["data"]
            if code == 14:
                pass
            elif code == 11:
                time.sleep(2)
            else:
                raise error_for(code or 9, str(answer.get("message", "")))
            if time.monotonic() >= deadline:
                raise SolveTimeoutError(job_id, timeout)

    def solve_recaptcha(
        self, task: str, grid: str, images: Union[Image, Sequence[Image]], timeout: float = DEFAULT_TIMEOUT
    ) -> GridResult:
        pictures = core.images_payload(images)
        core.check_grid(grid, len(pictures))
        job_id, data = self.solve("recaptcha", {"task": task, "grid": grid, "image_data": pictures}, timeout)
        return GridResult(job_id, grid, list(data))

    def solve_text(self, image: Image, timeout: float = DEFAULT_TIMEOUT) -> TextResult:
        job_id, data = self.solve("textcaptcha", {"image_data": core.images_payload(image)}, timeout)
        return TextResult(job_id, data[0])

    def solve_geetest(
        self, images: Union[Image, Sequence[Image]], task: str = "slide", timeout: float = DEFAULT_TIMEOUT
    ) -> GeetestResult:
        job_id, data = self.solve("geetest", {"task": task, "image_data": core.images_payload(images)}, timeout)
        return GeetestResult(job_id, float(data["x"]))

    def solve_funcaptcha(self, task: str, image: Image, match: bool = False, timeout: float = DEFAULT_TIMEOUT) -> GridResult:
        kind = "funcaptcha_match" if match else "funcaptcha"
        job_id, data = self.solve(kind, {"task": task, "image_data": core.images_payload(image)}, timeout)
        return GridResult(job_id, "funcaptcha", list(data))

    def status(self) -> Dict[str, Any]:
        body = self._request("GET", "/v1/status")
        if core.error_code(body):
            raise error_for(core.error_code(body), str(body.get("message", "")))
        return body

    def report_result(self, job_id: str, verdict: str, grid: str, round_index: Optional[int] = None) -> bool:
        payload: Dict[str, Any] = {"job_id": job_id, "verdict": verdict, "grid": grid}
        if round_index is not None:
            payload["round_index"] = round_index
        body = self._request("POST", "/v1/feedback", payload)
        if core.error_code(body):
            raise error_for(core.error_code(body), str(body.get("message", "")))
        return True

    def close(self) -> None:
        self._http.close()


class AsyncSolvecha:
    """Asynchronous client with the same methods as :class:`Solvecha`."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = core.DEFAULT_BASE_URL,
        http: Optional[httpx.AsyncClient] = None,
        poll_interval: float = POLL_INTERVAL,
    ):
        self._key = core.resolve_key(api_key)
        self._poll = poll_interval
        self._http = http or httpx.AsyncClient(timeout=30)
        self._base = base_url.rstrip("/")

    async def _request(self, method: str, path: str, json: Any = None) -> Dict[str, Any]:
        response = await self._http.request(method, self._base + path, json=json, headers=core.headers(self._key))
        return _body(response)

    async def solve(self, kind: str, payload: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT) -> tuple:
        job_id = core.job_id_from(await self._request("POST", f"/v1/recognition/{kind}", payload))
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            await asyncio.sleep(self._poll)
            answer = await self._request("GET", f"/v1/recognition/{kind}?id={job_id}")
            code = core.error_code(answer)
            if code == 0 and "data" in answer:
                return job_id, answer["data"]
            if code == 14:
                pass
            elif code == 11:
                await asyncio.sleep(2)
            else:
                raise error_for(code or 9, str(answer.get("message", "")))
            if loop.time() >= deadline:
                raise SolveTimeoutError(job_id, timeout)

    async def solve_recaptcha(
        self, task: str, grid: str, images: Union[Image, Sequence[Image]], timeout: float = DEFAULT_TIMEOUT
    ) -> GridResult:
        pictures = core.images_payload(images)
        core.check_grid(grid, len(pictures))
        job_id, data = await self.solve("recaptcha", {"task": task, "grid": grid, "image_data": pictures}, timeout)
        return GridResult(job_id, grid, list(data))

    async def solve_text(self, image: Image, timeout: float = DEFAULT_TIMEOUT) -> TextResult:
        job_id, data = await self.solve("textcaptcha", {"image_data": core.images_payload(image)}, timeout)
        return TextResult(job_id, data[0])

    async def solve_geetest(
        self, images: Union[Image, Sequence[Image]], task: str = "slide", timeout: float = DEFAULT_TIMEOUT
    ) -> GeetestResult:
        job_id, data = await self.solve("geetest", {"task": task, "image_data": core.images_payload(images)}, timeout)
        return GeetestResult(job_id, float(data["x"]))

    async def solve_funcaptcha(
        self, task: str, image: Image, match: bool = False, timeout: float = DEFAULT_TIMEOUT
    ) -> GridResult:
        kind = "funcaptcha_match" if match else "funcaptcha"
        job_id, data = await self.solve(kind, {"task": task, "image_data": core.images_payload(image)}, timeout)
        return GridResult(job_id, "funcaptcha", list(data))

    async def status(self) -> Dict[str, Any]:
        body = await self._request("GET", "/v1/status")
        if core.error_code(body):
            raise error_for(core.error_code(body), str(body.get("message", "")))
        return body

    async def report_result(self, job_id: str, verdict: str, grid: str, round_index: Optional[int] = None) -> bool:
        payload: Dict[str, Any] = {"job_id": job_id, "verdict": verdict, "grid": grid}
        if round_index is not None:
            payload["round_index"] = round_index
        body = await self._request("POST", "/v1/feedback", payload)
        if core.error_code(body):
            raise error_for(core.error_code(body), str(body.get("message", "")))
        return True

    async def aclose(self) -> None:
        await self._http.aclose()
