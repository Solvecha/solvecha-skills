"""Solvecha: captcha solving for scripts and AI agents."""

from .client import AsyncSolvecha, Solvecha
from .errors import (
    InvalidKeyError,
    InvalidRequestError,
    OutOfCreditError,
    RateLimitError,
    SolvechaError,
    SolveTimeoutError,
)
from .results import GeetestResult, GridResult, TextResult

__all__ = [
    "AsyncSolvecha",
    "Solvecha",
    "GridResult",
    "TextResult",
    "GeetestResult",
    "SolvechaError",
    "InvalidKeyError",
    "InvalidRequestError",
    "OutOfCreditError",
    "RateLimitError",
    "SolveTimeoutError",
]
__version__ = "0.1.0"
