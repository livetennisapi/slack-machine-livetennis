"""Pure formatting helpers that turn API payloads into Slack message text.

These functions contain no I/O so they can be unit-tested directly. They render
mrkdwn strings suitable for ``Message.say`` / ``Command.say``.
"""

from __future__ import annotations

from typing import Any

TENNIS = ":tennis:"


def _player_name(match: dict[str, Any], key: str) -> str:
    players = match.get("players") or {}
    player = players.get(key) or {}
    return player.get("name") or "?"


def _pair(value: Any) -> tuple[Any, Any] | None:
    """Coerce a score element into a ``(p1, p2)`` pair, or ``None``."""
    if isinstance(value, dict):
        for a, b in (("p1", "p2"), ("home", "away"), ("1", "2")):
            if a in value or b in value:
                return value.get(a), value.get(b)
        return None
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return value[0], value[1]
    return None


def _score_line(score: dict[str, Any] | None) -> str:
    """Build a compact score string, e.g. ``6-4 3-2 | 30-15``."""
    if not score:
        return ""
    parts: list[str] = []

    sets_str = []
    for game in score.get("games") or []:
        pair = _pair(game)
        if pair is not None:
            sets_str.append(f"{pair[0]}-{pair[1]}")
    if sets_str:
        parts.append(" ".join(sets_str))

    points_pair = _pair(score.get("points"))
    if points_pair is not None:
        parts.append(f"{points_pair[0]}-{points_pair[1]}")

    return " | ".join(parts)


def _serving_marker(match: dict[str, Any], key: str) -> str:
    score = match.get("score") or {}
    server = score.get("server")
    mapping = {1: "p1", 2: "p2"}
    if mapping.get(server) == key:
        return f" {TENNIS}"
    return ""


def format_live_matches(matches: list[dict[str, Any]]) -> str:
    """Render the list of live matches as a Slack mrkdwn string."""
    if not matches:
        return "No live matches right now. :sleeping:"

    lines = [f"*Live matches* ({len(matches)}):"]
    for match in matches:
        p1 = _player_name(match, "p1")
        p2 = _player_name(match, "p2")
        line = f"• *{p1}*{_serving_marker(match, 'p1')} vs *{p2}*{_serving_marker(match, 'p2')}"

        score_line = _score_line(match.get("score"))
        if score_line:
            line += f"  —  {score_line}"

        flags = []
        if match.get("break_point"):
            flags.append("break point")
        status = (match.get("status") or "").lower()
        if status in ("retired", "walkover") or match.get("retirement") or match.get("walkover"):
            flags.append(status or "walkover")
        if flags:
            line += f"  _({', '.join(flags)})_"

        lines.append(line)
    return "\n".join(lines)


def format_rankings(players: list[dict[str, Any]], limit: int = 10) -> str:
    """Render the top ranked players."""
    if not players:
        return "No ranking data available right now."

    lines = [f"*Top {min(limit, len(players))} players:*"]
    for player in players[:limit]:
        rank = player.get("ranking", "?")
        name = player.get("name", "?")
        elo = player.get("elo")
        elo_str = f"  ·  Elo {round(elo)}" if isinstance(elo, (int, float)) else ""
        lines.append(f"{rank}. *{name}*{elo_str}")
    return "\n".join(lines)


def format_player(players: list[dict[str, Any]], query: str) -> str:
    """Render the best match for a player search."""
    if not players:
        return f"No player found matching *{query}*."

    player = players[0]
    name = player.get("name", query)
    rank = player.get("ranking")
    elo = player.get("elo")

    bits = [f"*{name}*"]
    if rank is not None:
        bits.append(f"Ranking: *#{rank}*")
    if isinstance(elo, (int, float)):
        bits.append(f"Elo: *{round(elo)}*")

    result = "  ·  ".join(bits)
    if len(players) > 1:
        others = ", ".join(p.get("name", "?") for p in players[1:4])
        result += f"\n_Other matches: {others}_"
    return result


def format_fixtures(fixtures: list[dict[str, Any]], limit: int = 10) -> str:
    """Render upcoming fixtures."""
    if not fixtures:
        return "No upcoming fixtures found."

    lines = [f"*Upcoming fixtures* (next {min(limit, len(fixtures))}):"]
    for fixture in fixtures[:limit]:
        p1 = _player_name(fixture, "p1")
        p2 = _player_name(fixture, "p2")
        when = fixture.get("start_time") or fixture.get("scheduled") or fixture.get("date")
        tournament = fixture.get("tournament") or fixture.get("event")
        line = f"• *{p1}* vs *{p2}*"
        meta = [str(x) for x in (tournament, when) if x]
        if meta:
            line += f"  —  {'  ·  '.join(meta)}"
        lines.append(line)
    return "\n".join(lines)
