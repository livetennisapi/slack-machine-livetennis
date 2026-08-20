"""slack-machine-livetennis: live tennis scores, rankings and fixtures for Slack.

Data source: the Live Tennis API (https://livetennisapi.com). A free key is
available with no card required.
"""

from sm_livetennis.client import (
    ApiError,
    AuthError,
    LiveTennisClient,
    LiveTennisError,
    RateLimitError,
)
from sm_livetennis.plugin import LiveTennis

__all__ = [
    "LiveTennis",
    "LiveTennisClient",
    "LiveTennisError",
    "AuthError",
    "RateLimitError",
    "ApiError",
]

__version__ = "0.1.0"
