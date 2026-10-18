"""Ready-made agent tools for Solvecha.

Every function returns a plain dict. Errors never raise inside a tool: the dict
holds an ``error`` text that tells the model what to do next.

    from solvecha import Solvecha
    from solvecha.tools import langchain_tools
    tools = langchain_tools(Solvecha())

The framework packages are imported only when you call its function.
"""
import functools
import json
from typing import Any, Callable, Dict, List, Optional

from .client import AsyncSolvecha, Solvecha
from .errors import SolvechaError

Func = Callable[..., Dict[str, Any]]

TOOL_SPECS: List[Dict[str, Any]] = [
    {
        "name": "solve_recaptcha_grid",
        "description": (
            "Solve a reCAPTCHA v2 image challenge from a picture of the grid. Returns selected_tiles: the tiles "
            "to click, counted from 1, left to right, top to bottom. Costs one credit per successful solve."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The instruction text, e.g. 'Select all images with buses'."},
                "grid": {"type": "string", "enum": ["3x3", "4x4", "1x1"], "description": "Layout of the challenge."},
                "image": {"type": "string", "description": "Path of a PNG/JPEG file, or base64 of the grid picture."},
            },
            "required": ["task", "grid", "image"],
        },
    },
    {
        "name": "solve_text_captcha",
        "description": "Read a picture of distorted text. Returns the case-sensitive text. Costs one credit per successful solve.",
        "parameters": {
            "type": "object",
            "properties": {"image": {"type": "string", "description": "Path of a picture file, or base64."}},
            "required": ["image"],
        },
    },
    {
        "name": "get_account_status",
        "description": "Show the plan, the solves left today and the balance. Free.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "report_result",
        "description": "Tell Solvecha whether a reCAPTCHA answer was accepted or rejected. Free and optional.",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "verdict": {"type": "string", "enum": ["accepted", "rejected"]},
                "grid": {"type": "string", "enum": ["3x3", "4x4", "1x1"]},
            },
            "required": ["job_id", "verdict", "grid"],
        },
    },
]


def _guard(fn: Func) -> Func:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        try:
            return fn(*args, **kwargs)
        except (SolvechaError, ValueError, OSError) as error:
            return {"error": str(error)}

    return wrapper


def functions(client: Solvecha) -> Dict[str, Func]:
    """The tools as plain Python functions (with type hints and docstrings)."""

    @_guard
    def solve_recaptcha_grid(task: str, grid: str, image: str) -> Dict[str, Any]:
        """Solve a reCAPTCHA v2 image challenge. Returns selected_tiles: tiles to click, counted from 1, left to right, top to bottom.

        Args:
            task: The instruction text, e.g. 'Select all images with buses'.
            grid: '3x3', '4x4' or '1x1'.
            image: Path of a PNG/JPEG file, or base64 of the grid picture.
        """
        result = client.solve_recaptcha(task, grid, image)
        return {"job_id": result.job_id, "selected_tiles": result.tiles, "positions": result.positions}

    @_guard
    def solve_text_captcha(image: str) -> Dict[str, Any]:
        """Read a picture of distorted text and return the case-sensitive text.

        Args:
            image: Path of a picture file, or base64.
        """
        result = client.solve_text(image)
        return {"job_id": result.job_id, "text": result.text}

    @_guard
    def get_account_status() -> Dict[str, Any]:
        """Show the plan, the solves left today and the balance. Free."""
        body = client.status()
        return {k: body.get(k) for k in ("plan", "status", "credit", "quota", "balance_usd", "ttl")}

    @_guard
    def report_result(job_id: str, verdict: str, grid: str) -> Dict[str, Any]:
        """Tell Solvecha whether a reCAPTCHA answer was accepted or rejected. Free.

        Args:
            job_id: The job_id from solve_recaptcha_grid.
            verdict: 'accepted' or 'rejected'.
            grid: '3x3', '4x4' or '1x1'.
        """
        return {"recorded": client.report_result(job_id, verdict, grid)}

    return {f.__name__: f for f in (solve_recaptcha_grid, solve_text_captcha, get_account_status, report_result)}


# ---- OpenAI function calling (Chat Completions and Responses) ----

def openai_tools(client: Solvecha) -> tuple:
    """Return (tools, handle). Pass ``tools`` to the API; call ``handle(name, arguments_json)`` for each tool call.

    ``tools`` uses the Chat Completions shape. For the Responses API flatten it:
    ``[{"type": "function", **t["function"]} for t in tools]``.
    """
    funcs = functions(client)
    tools = [{"type": "function", "function": dict(spec)} for spec in TOOL_SPECS]

    def handle(name: str, arguments: str) -> str:
        if name not in funcs:
            return json.dumps({"error": f"unknown tool {name}"})
        try:
            kwargs = json.loads(arguments or "{}")
        except ValueError:
            return json.dumps({"error": "arguments are not valid JSON"})
        try:
            return json.dumps(funcs[name](**kwargs))
        except TypeError as error:
            return json.dumps({"error": f"bad arguments: {error}"})

    return tools, handle


def openai_agents_tools(client: Solvecha) -> list:
    """Tools for the OpenAI Agents SDK (``pip install openai-agents``)."""
    from agents import function_tool

    return [function_tool(f) for f in functions(client).values()]


def langchain_tools(client: Solvecha) -> list:
    """Tools for LangChain and LangGraph (``pip install langchain-core``)."""
    from langchain_core.tools import StructuredTool

    return [StructuredTool.from_function(f, name=f.__name__, description=(f.__doc__ or "").split("\n\n")[0]) for f in functions(client).values()]


def crewai_tools(client: Solvecha) -> list:
    """Tools for CrewAI (``pip install crewai``)."""
    from crewai.tools import tool

    return [tool(f.__name__)(f) for f in functions(client).values()]


def llamaindex_tools(client: Solvecha) -> list:
    """Tools for LlamaIndex (``pip install llama-index-core``)."""
    from llama_index.core.tools import FunctionTool

    return [FunctionTool.from_defaults(fn=f) for f in functions(client).values()]


def browser_use_tools(client: AsyncSolvecha, tools: Optional[Any] = None) -> Any:
    """Add a "solve the reCAPTCHA in the current tab" action to a Browser Use ``Tools`` object.

    The action screenshots the reCAPTCHA challenge window (or the whole viewport when
    none is found), solves it and returns the tiles to click. The agent clicks them.
    """
    from .browser_use_action import register

    return register(client, tools)
