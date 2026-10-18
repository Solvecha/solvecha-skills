# solvecha (Python)

A small client for the [Solvecha](https://solvecha.com) captcha API, plus ready-made tools for AI agent frameworks: OpenAI function calling and the Agents SDK, LangChain, CrewAI, LlamaIndex and Browser Use.

```bash
pip install solvecha                  # client only (needs httpx)
pip install "solvecha[langchain]"     # or openai, crewai, llamaindex, browser-use
export SOLVECHA_API_KEY=slv_...       # create a key at https://solvecha.com/dashboard
```

## Client

```python
from solvecha import Solvecha

client = Solvecha()  # reads SOLVECHA_API_KEY
result = client.solve_recaptcha("Select all images with buses", "3x3", "grid.png")
print(result.tiles)      # [2, 4, 5], counted from 1, left to right, top to bottom
print(result.positions)  # ['row 1, column 2', ...]
client.report_result(result.job_id, "accepted", "3x3")  # optional, free
```

`images` can be a file path, bytes, base64 text or a data URL. `AsyncSolvecha` has the same methods. Other methods: `solve_text`, `solve_geetest`, `solve_funcaptcha`, `status`. Errors raise `SolvechaError` subclasses with the API code (`InvalidKeyError` 15, `OutOfCreditError` 16, `RateLimitError` 11).

## Agent tools

```python
from solvecha import Solvecha
from solvecha.tools import openai_tools, openai_agents_tools, langchain_tools, crewai_tools, llamaindex_tools

client = Solvecha()
tools, handle = openai_tools(client)     # Chat Completions: pass tools=tools, answer calls with handle(name, args_json)
agents_sdk = openai_agents_tools(client) # OpenAI Agents SDK
lc = langchain_tools(client)             # LangChain / LangGraph
crew = crewai_tools(client)              # CrewAI
li = llamaindex_tools(client)            # LlamaIndex
```

Tools never raise: a failure comes back as `{"error": "..."}` with advice for the model.

### Browser Use

```python
from browser_use import Agent, Browser, ChatBrowserUse
from solvecha import AsyncSolvecha
from solvecha.tools import browser_use_tools

tools = browser_use_tools(AsyncSolvecha())   # adds the action solve_recaptcha_in_tab
agent = Agent(task="...", llm=ChatBrowserUse(), browser=Browser(), tools=tools)
```

The action crops the screenshot to the reCAPTCHA challenge window and returns the tiles to click.

## Or use MCP

No code needed: `https://api.solvecha.com/mcp` with `Authorization: Bearer <key>`. See https://solvecha.com/docs/mcp-server.

## Develop

```bash
pip install -e ".[test]" && pytest
python -m build   # needs: pip install build
```
