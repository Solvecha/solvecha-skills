# Solvecha for AI agents

Skills and framework tools for [Solvecha](https://solvecha.com), a captcha solving API (reCAPTCHA image grids, text captchas, GeeTest sliders, FunCAPTCHA).

| Path | What |
|---|---|
| `skills/solvecha/` | Agent skill (`SKILL.md`, scripts in Python and Node.js, references). Works in Claude Code, Claude Desktop, OpenClaw and Hermes Agent. |
| `python/` | `solvecha` Python package: API client and tools for OpenAI, LangChain, CrewAI, LlamaIndex and Browser Use. |

The fastest way for most agents is the remote MCP server: `https://api.solvecha.com/mcp` (header `Authorization: Bearer <key>`). See https://solvecha.com/docs/ai-agents.

You need an API key from https://solvecha.com/dashboard. The free tier has 100 successful solves a day. **Never commit a key.** The skill and the package read `SOLVECHA_API_KEY`.

## Install the skill

```bash
# Claude Code (personal)
cp -r skills/solvecha ~/.claude/skills/solvecha

# OpenClaw
cp -r skills/solvecha ~/.openclaw/skills/solvecha
# or from Git: openclaw skills install git:<owner>/<repo>

# Hermes Agent
hermes skills tap add Solvecha/solvecha-skills
hermes skills install solvecha
# or by hand (the folder under skills/ is the install name): cp -r skills/solvecha ~/.hermes/skills/solvecha
```

One command for the agents on your machine (Claude Code, Cursor, Codex and others), through [skills.sh](https://skills.sh):

```bash
npx skills add Solvecha/solvecha-skills
```

Claude Desktop and claude.ai: zip the `solvecha` folder (the folder itself at the top of the zip) and upload it under Customize, Skills.

Validate with the official checker: `pip install "git+https://github.com/agentskills/agentskills#subdirectory=skills-ref" && skills-ref validate skills/solvecha`.

## Python package

```bash
pip install solvecha
pip install "solvecha[langchain]"   # or openai, crewai, llamaindex, browser-use
```

On PyPI: https://pypi.org/project/solvecha/. See [python/README.md](python/README.md) for the client and the framework tools.

## Releases

A published GitHub release uploads the Python package to PyPI (`.github/workflows/publish.yml`, Trusted Publishing, no stored token). The skill is not on npm or ClawHub; it installs from this repository with `npx skills add` and the Hermes tap.

MIT licensed. Solvecha is not affiliated with CloakHQ, NopeCHA, 2Captcha or CapSolver.
