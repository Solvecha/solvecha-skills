from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

_COLUMNS = {"3x3": 3, "4x4": 4}


@dataclass
class GridResult:
    """Answer for an image grid. ``tiles`` are counted from 1, left to right, top to bottom."""

    job_id: str
    grid: str
    answer: List[bool]
    tiles: List[int] = field(init=False)

    def __post_init__(self) -> None:
        self.tiles = [i + 1 for i, picked in enumerate(self.answer) if picked]

    @property
    def positions(self) -> List[str]:
        columns = _COLUMNS.get(self.grid)
        if not columns:
            return []
        return [f"row {(t - 1) // columns + 1}, column {(t - 1) % columns + 1}" for t in self.tiles]


@dataclass
class TextResult:
    job_id: str
    text: str


@dataclass
class GeetestResult:
    """``offset_percent`` is the drag distance as a percentage of the background width."""

    job_id: str
    offset_percent: float
