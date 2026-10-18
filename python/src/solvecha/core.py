"""Pure helpers shared by the sync and the async client."""
from __future__ import annotations

import base64
import os
from typing import Any, Dict, List, Optional, Sequence, Union

from .errors import SolvechaError, error_for

DEFAULT_BASE_URL = "https://api.solvecha.com"
GRIDS = ("3x3", "4x4", "1x1")
Image = Union[str, bytes, "os.PathLike[str]"]


def to_base64(image: Image) -> str:
    """Accept a file path, raw bytes, base64 text or a data: URL and return plain base64."""
    if isinstance(image, (bytes, bytearray)):
        return base64.b64encode(bytes(image)).decode()
    text = os.fspath(image)
    if text.startswith("data:"):
        return text.split(",", 1)[1]
    if len(text) < 1024 and os.path.isfile(text):
        with open(text, "rb") as handle:
            return base64.b64encode(handle.read()).decode()
    return "".join(text.split())


def images_payload(images: Union[Image, Sequence[Image]]) -> List[str]:
    if isinstance(images, (str, bytes, bytearray)) or hasattr(images, "__fspath__"):
        images = [images]  # type: ignore[list-item]
    return [to_base64(i) for i in images]  # type: ignore[union-attr]


def check_grid(grid: str, count: int) -> None:
    if grid not in GRIDS:
        raise ValueError(f"grid must be one of {GRIDS}, got {grid!r}")
    if grid != "1x1" and count != 1:
        raise ValueError(f"grid {grid} needs exactly one picture of the whole grid, got {count}")
    if grid == "1x1" and not 1 <= count <= 9:
        raise ValueError("grid 1x1 needs 1 to 9 tile pictures")


def error_code(body: Dict[str, Any]) -> int:
    value = body.get("error")
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 9


def job_id_from(body: Dict[str, Any]) -> str:
    code = error_code(body)
    if code:
        raise error_for(code, str(body.get("message", "")))
    data = body.get("data")
    if not isinstance(data, str) or not data:
        raise SolvechaError(9, "no job id in the answer")
    return data


def headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "User-Agent": "solvecha-python/0.1"}


def resolve_key(api_key: Optional[str]) -> str:
    key = api_key or os.environ.get("SOLVECHA_API_KEY", "")
    if not key:
        raise error_for(15, "no key")
    return key
