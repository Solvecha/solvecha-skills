---
name: solvecha
description: Solve CAPTCHAs with the Solvecha API (reCAPTCHA v2 image grids, text captchas, GeeTest sliders, FunCAPTCHA). Use when a browser task is blocked by a captcha, an image challenge appears, or the user asks to solve or bypass a captcha on a site they may automate.
license: MIT
compatibility: Needs a Solvecha API key in SOLVECHA_API_KEY and network access to api.solvecha.com. Works in Claude Code, Claude Desktop, OpenClaw and Hermes Agent.
metadata:
  author: solvecha
  version: "1.0"
  homepage: https://solvecha.com/docs/ai-agents
---

# Solvecha captcha solver

Solvecha answers image captchas. It returns an answer for the pictures you send. It does not return finished reCAPTCHA tokens, so the agent (or the browser extension) must click the tiles.

## 1. Check what is available

Work through this list and use the first way that applies.

1. **The Solvecha browser extension is loaded in the browser you control.** Do nothing. It reads reCAPTCHA image challenges, asks the API and clicks the tiles. Wait a few seconds and check whether the page moved on. See `references/extension-cdp.md` to set it up.
2. **An MCP server called `solvecha` is connected.** Use its tools:
   - `solve_recaptcha_grid` (`task`, `grid`, `images`) returns `selected_tiles`.
   - `solve_text_captcha`, `solve_geetest_slider`, `solve_funcaptcha` for the other types.
   - `get_account_status` shows the credit. `report_result` sends Google's verdict.
3. **Neither.** Run the scripts in `scripts/` (Python or Node.js) or call the REST API. They need `SOLVECHA_API_KEY`.

If no key exists, tell the user to create one at https://solvecha.com/dashboard (free tier: 100 successful solves a day). Never print the key.

## 2. Solve a reCAPTCHA image challenge

1. Read the instruction text, for example "Select all images with buses".
2. Take a screenshot of only the grid, or of the challenge window if you cannot crop. Note the layout: `3x3` or `4x4`.
3. Solve it:
   ```bash
   python3 scripts/solve_recaptcha.py --task "Select all images with buses" --grid 3x3 --image grid.png
   # or: node scripts/solve_recaptcha.mjs --task "..." --grid 3x3 --image grid.png
   ```
   The output is a JSON object with `selected_tiles` (counted from 1, left to right, top to bottom) and a `job_id`.
4. Click those tiles. Some 3x3 challenges replace a clicked tile with a new picture. Screenshot each new tile and solve it again with `--grid 1x1`.
5. Press Verify. If a new round appears, repeat from step 1.
6. Send the verdict (free, optional): `python3 scripts/solve_recaptcha.py --report JOB_ID --verdict accepted --grid 3x3`.

## 3. Other captcha types

| Type | API path | Send | Answer |
|---|---|---|---|
| Text captcha | `/v1/recognition/textcaptcha` | `image_data: [base64]` | `["K7m2Q"]` |
| GeeTest slider | `/v1/recognition/geetest` | `task: "slide"`, `image_data: [background, piece]` | `{"x": 42.5}` percent of the background width |
| FunCAPTCHA tiles | `/v1/recognition/funcaptcha` | `task`, `image_data: [grid]` | list of booleans |
| FunCAPTCHA match | `/v1/recognition/funcaptcha_match` | `task`, `image_data: [image]` | list of booleans |

Details: https://solvecha.com/docs/captcha-types/recaptcha and `references/api.md`.

## 4. Cost and errors

- A successful solve costs one credit: free tier first, then the prepaid balance ($0.10 per 1,000) or the plan quota. Failed solves cost nothing.
- Error `15`: wrong or missing key. Ask the user.
- Error `16`: out of credit. Tell the user to top up. Do not retry.
- Error `11`: rate limit. Wait 30 seconds.
- Error `9`, or no answer in 45 seconds: retry once with a fresh screenshot.
- If a challenge is rejected twice in a row, stop and report it. Do not loop.

## 5. Rules

- Use this only on sites where automation is allowed (https://solvecha.com/legal/acceptable-use).
- Never write the API key into files, logs or messages.
- Fewer captchas appear in a stealth browser such as CloakBrowser. Solvecha is not affiliated with CloakHQ.
