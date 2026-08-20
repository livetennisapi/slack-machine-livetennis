"""Live Tennis plugin for Slack Machine.

Brings live tennis match state, player rankings/Elo and upcoming fixtures into
Slack, backed by the Live Tennis API (https://livetennisapi.com).

Data source disclosure: this plugin is developed by the Live Tennis API team and
talks to the Live Tennis API. A free key (live scores, match state, players,
fixtures — no card required) is available at
https://livetennisapi.com/subscribe/free
"""

from __future__ import annotations

from structlog.stdlib import BoundLogger, get_logger

from machine.plugins.base import MachineBasePlugin
from machine.plugins.command import Command
from machine.plugins.decorators import command, respond_to
from machine.plugins.message import Message

from sm_livetennis import formatting
from sm_livetennis.client import (
    ApiError,
    AuthError,
    LiveTennisClient,
    RateLimitError,
)

logger = get_logger(__name__)

API_KEY_SETTING = "LIVETENNIS_API_KEY"

NO_KEY_MESSAGE = (
    ":warning: No Live Tennis API key configured. Add a "
    f"`{API_KEY_SETTING}` setting (env var `SM_{API_KEY_SETTING}`) to your bot. "
    "Grab a free key — no card required — at "
    "<https://livetennisapi.com/subscribe/free>."
)

HELP_TEXT = (
    ":tennis: *Live Tennis* — live scores, rankings & fixtures.\n"
    "`/tennis live` — matches in progress right now\n"
    "`/tennis rankings` — top ranked players (with Elo)\n"
    "`/tennis player <name>` — look up a player's ranking & Elo\n"
    "`/tennis next` — upcoming fixtures\n"
    "`/tennis help` — this message\n"
    "_Data: <https://livetennisapi.com|Live Tennis API>. "
    "Free key at <https://livetennisapi.com/subscribe/free>._"
)


class LiveTennis(MachineBasePlugin):
    """Live tennis scores, rankings and fixtures for Slack."""

    def _build_client(self) -> LiveTennisClient | None:
        """Build a client from settings, or ``None`` if no key is configured."""
        api_key = self.settings.get(API_KEY_SETTING)
        if not api_key:
            return None
        base_url = self.settings.get("LIVETENNIS_BASE_URL")
        if base_url:
            return LiveTennisClient(api_key, base_url=base_url)
        return LiveTennisClient(api_key)

    async def _handle(self, text: str) -> str:
        """Route a command body to a formatted Slack response string.

        This is pure enough to unit-test: given the text, it performs the API
        call (via the client) and returns the message text, translating every
        error into a friendly, actionable message.
        """
        text = (text or "").strip()
        args = text.split()
        sub = args[0].lower() if args else "help"

        if sub in ("help", "-h", "--help", "?"):
            return HELP_TEXT

        client = self._build_client()
        if client is None:
            return NO_KEY_MESSAGE

        try:
            if sub in ("live", "scores", "now"):
                return formatting.format_live_matches(await client.live_matches())
            if sub in ("rankings", "ranking", "top", "rank"):
                return formatting.format_rankings(await client.rankings())
            if sub in ("player", "search", "who"):
                query = " ".join(args[1:]).strip()
                if not query:
                    return "Usage: `/tennis player <name>` — e.g. `/tennis player alcaraz`"
                return formatting.format_player(await client.search_players(query), query)
            if sub in ("next", "fixtures", "upcoming", "schedule"):
                return formatting.format_fixtures(await client.fixtures())
            return f"Unknown subcommand `{sub}`.\n\n{HELP_TEXT}"
        except AuthError:
            return (
                ":lock: The Live Tennis API rejected the configured key. "
                "Check `LIVETENNIS_API_KEY`, or get a free key at "
                "<https://livetennisapi.com/subscribe/free>."
            )
        except RateLimitError:
            return (
                ":hourglass_flowing_sand: Rate limit reached on the Live Tennis API "
                "(free tier is 30 req/min, 100/day). Please try again shortly."
            )
        except ApiError as exc:
            logger.warning("live tennis api error", error=str(exc))
            return ":x: The Live Tennis API is unavailable right now. Please try again later."

    @command("/tennis")
    async def tennis_command(self, command: Command, logger: BoundLogger) -> None:
        """/tennis: live scores, rankings, player lookup and fixtures."""
        logger.info("tennis command", text=command.text)
        response = await self._handle(command.text)
        await command.say(text=response, ephemeral=False)

    @respond_to(r"\btennis\b\s*(?P<query>.*)")
    async def tennis_mention(self, msg: Message, query: str = "", logger: BoundLogger = None) -> None:
        """tennis <live|rankings|player <name>|next>: same as /tennis, via mention."""
        if logger is not None:
            logger.info("tennis mention", query=query)
        response = await self._handle(query)
        await msg.say(response)
