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

# Hermes Agent (the folder under skills/ is the install name)
cp -r skills/solvecha ~/.hermes/skills/solvecha
# or, once this repo is public: hermes skills tap add <owner>/<repo> && hermes skills install solvecha
```

Claude Desktop and claude.ai: zip the `solvecha` folder (the folder itself at the top of the zip) and upload it under Customize, Skills.

Validate with the official checker: `pip install "git+https://github.com/agentskills/agentskills#subdirectory=skills-ref" && skills-ref validate skills/solvecha`.

## Python package

See [python/README.md](python/README.md).

## Not published yet

Nothing here is on PyPI, npm, ClawHub or a skills catalog. See the publishing checklist in the Solvecha task report.

MIT licensed. Solvecha is not affiliated with CloakHQ, NopeCHA, 2Captcha or CapSolver.
