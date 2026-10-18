"""Build the tools with each real framework. Skipped when the framework is not installed."""
import base64
import json

import httpx
import pytest

from solvecha import AsyncSolvecha, Solvecha
from solvecha.tools import (
    browser_use_tools,
    crewai_tools,
    langchain_tools,
    llamaindex_tools,
    openai_agents_tools,
)
from test_client import KEY, PNG, FakeAPI


def make():
    return Solvecha(KEY, http=httpx.Client(transport=httpx.MockTransport(FakeAPI())), poll_interval=0)


def test_langchain():
    pytest.importorskip("langchain_core")
    tools = {t.name: t for t in langchain_tools(make())}
    assert set(tools) == {"solve_recaptcha_grid", "solve_text_captcha", "get_account_status", "report_result"}
    out = tools["solve_recaptcha_grid"].invoke({"task": "t", "grid": "3x3", "image": PNG})
    assert out["selected_tiles"] == [2, 4, 5]
    assert tools["solve_recaptcha_grid"].args["grid"]["type"] == "string"


def test_llamaindex():
    pytest.importorskip("llama_index.core")
    tools = {t.metadata.name: t for t in llamaindex_tools(make())}
    out = tools["solve_recaptcha_grid"](task="t", grid="3x3", image=PNG)
    assert "[2, 4, 5]" in str(out)


def test_crewai():
    pytest.importorskip("crewai")
    tools = {t.name: t for t in crewai_tools(make())}
    assert any("solve_recaptcha_grid" in n.replace(" ", "_").lower() for n in tools)
    tool = next(t for n, t in tools.items() if "recaptcha" in n.lower())
    assert "[2, 4, 5]" in str(tool.run(task="t", grid="3x3", image=PNG))


def test_openai_agents():
    pytest.importorskip("agents")
    tools = openai_agents_tools(make())
    names = {t.name for t in tools}
    assert "solve_recaptcha_grid" in names
    schema = next(t for t in tools if t.name == "solve_recaptcha_grid").params_json_schema
    assert set(schema["required"]) == {"task", "grid", "image"}


async def test_browser_use_action_is_registered():
    pytest.importorskip("browser_use")
    client = AsyncSolvecha(KEY, http=httpx.AsyncClient(transport=httpx.MockTransport(FakeAPI())), poll_interval=0)
    tools = browser_use_tools(client)
    assert "solve_recaptcha_in_tab" in tools.registry.registry.actions
