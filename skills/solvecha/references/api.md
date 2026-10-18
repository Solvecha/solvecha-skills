# Solvecha API quick reference

Base URL: `https://api.solvecha.com`. Header: `Authorization: Bearer slv_...`.

- `POST /v1/recognition/{recaptcha|textcaptcha|geetest|funcaptcha|funcaptcha_match}` creates a job and returns `{"data": "<job id>"}`.
- `GET /v1/recognition/<type>?id=<job id>` returns the answer, or error `14` ("Incomplete job") while it works. Poll once a second.
- `GET /v1/status` shows the plan, credit and balance.
- `POST /v1/feedback` with `{job_id, verdict: accepted|rejected, grid}` reports Google's verdict. Free.

Request bodies:

| Type | Fields |
|---|---|
| `recaptcha` | `task`, `grid` (`3x3`, `4x4`, `1x1`), `image_data` (one grid picture; 1 to 9 tiles for `1x1`) |
| `textcaptcha` | `image_data` (one picture) |
| `geetest` | `task: "slide"`, `image_data` (screenshot, or background then piece) |
| `funcaptcha`, `funcaptcha_match` | `task`, `image_data` (one picture) |

Errors: `9` unknown or unsolvable, `10` invalid request, `11` rate limit, `14` not ready, `15` invalid key, `16` out of credit.

Full documentation: https://solvecha.com/docs and https://solvecha.com/llms.txt.
