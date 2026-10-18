# No "from __future__ import annotations" here: Browser Use reads the real
# annotation objects to inject its browser_session argument.
import json
from typing import Any, Optional

from browser_use import ActionResult, BrowserSession, Tools

from .client import AsyncSolvecha
from .errors import SolvechaError

FIND_CHALLENGE = """(() => {
    const f = document.querySelector('iframe[src*="recaptcha/api2/bframe"], iframe[src*="recaptcha/enterprise/bframe"]');
    if (!f) return null;
    const r = f.getBoundingClientRect();
    return r.width > 50 && r.height > 50 ? JSON.stringify({x: r.x, y: r.y, width: r.width, height: r.height}) : null;
})()"""


def register(client: AsyncSolvecha, tools: Optional[Any] = None) -> Any:
    tools = tools or Tools()

    @tools.action(
        description=(
            "Solve the reCAPTCHA v2 image challenge that is open in the current tab. Pass the instruction text "
            "(e.g. 'Select all images with buses') and the grid ('3x3' or '4x4'). Returns the tile numbers to click, "
            "counted from 1, left to right, top to bottom, and a job id."
        )
    )
    async def solve_recaptcha_in_tab(task: str, grid: str, browser_session: BrowserSession) -> ActionResult:
        clip = None
        try:
            page = await browser_session.must_get_current_page()
            raw = await page.evaluate(FIND_CHALLENGE)
            if isinstance(raw, str) and raw not in ("", "null"):
                box = json.loads(raw)
                clip = {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"], "scale": 1}
        except Exception:  # noqa: BLE001 - cropping is optional
            clip = None
        png = await browser_session.take_screenshot(clip=clip) if clip else await browser_session.take_screenshot()
        try:
            result = await client.solve_recaptcha(task, grid, png)
        except (SolvechaError, ValueError) as error:
            return ActionResult(error=str(error))
        return ActionResult(
            extracted_content=f"Click tiles {result.tiles} ({'; '.join(result.positions)}), then press Verify. job_id={result.job_id}"
        )

    return tools
