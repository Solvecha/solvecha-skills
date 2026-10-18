from __future__ import annotations

KEY_HELP = "Create a key at https://solvecha.com/dashboard and set SOLVECHA_API_KEY."

_ADVICE = {
    9: "Temporary error, or the image could not be solved. Retry once with a fresh image. You are not charged.",
    10: "Invalid request. Check the task text, the grid and the images.",
    11: "Rate limit reached. Wait 10 to 60 seconds and try again.",
    15: "The API key is missing or wrong. " + KEY_HELP,
    16: "Out of credit. Top up the balance or pick a plan at https://solvecha.com/dashboard. Do not retry.",
}


class SolvechaError(Exception):
    """An error answer of the Solvecha API. ``code`` is the API error code."""

    def __init__(self, code: int, message: str = ""):
        self.code = code
        self.api_message = message
        super().__init__(f"Solvecha error {code}: {_ADVICE.get(code, message or 'unexpected answer')}")


class InvalidRequestError(SolvechaError):
    pass


class RateLimitError(SolvechaError):
    pass


class InvalidKeyError(SolvechaError):
    pass


class OutOfCreditError(SolvechaError):
    pass


class SolveTimeoutError(SolvechaError, TimeoutError):
    def __init__(self, job_id: str, seconds: float):
        self.job_id = job_id
        SolvechaError.__init__(self, 14, "")
        self.args = (f"No answer within {seconds:g} seconds (job {job_id}). You were not charged.",)


_BY_CODE = {10: InvalidRequestError, 11: RateLimitError, 15: InvalidKeyError, 16: OutOfCreditError}


def error_for(code: int, message: str = "") -> SolvechaError:
    return _BY_CODE.get(code, SolvechaError)(code, message)
