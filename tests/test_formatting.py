from sm_livetennis import formatting

LIVE_MATCH = {
    "id": "m1",
    "status": "live",
    "players": {"p1": {"name": "Carlos Alcaraz"}, "p2": {"name": "Jannik Sinner"}},
    "break_point": True,
    "score": {
        "sets": [[1, 0]],
        "games": [[6, 4], [3, 2]],
        "points": ["30", "15"],
        "server": 1,
    },
}


def test_format_live_matches_empty():
    out = formatting.format_live_matches([])
    assert "No live matches" in out


def test_format_live_matches_renders_players_score_server_and_flags():
    out = formatting.format_live_matches([LIVE_MATCH])
    assert "Carlos Alcaraz" in out
    assert "Jannik Sinner" in out
    # set-by-set from games + current points
    assert "6-4 3-2" in out
    assert "30-15" in out
    # break point flag
    assert "break point" in out
    # server 1 == p1 gets the tennis marker somewhere on the line
    assert ":tennis:" in out
    # count header
    assert "(1)" in out


def test_format_live_matches_walkover_flag():
    match = {
        "status": "walkover",
        "players": {"p1": {"name": "A"}, "p2": {"name": "B"}},
    }
    out = formatting.format_live_matches([match])
    assert "walkover" in out.lower()


def test_format_rankings():
    players = [
        {"name": "Novak Djokovic", "ranking": 1, "elo": 2140.7},
        {"name": "Carlos Alcaraz", "ranking": 2, "elo": 2110},
    ]
    out = formatting.format_rankings(players)
    assert "1. *Novak Djokovic*" in out
    assert "Elo 2141" in out  # rounded
    assert "2. *Carlos Alcaraz*" in out


def test_format_rankings_empty():
    assert "No ranking data" in formatting.format_rankings([])


def test_format_player_found():
    players = [{"name": "Iga Swiatek", "ranking": 1, "elo": 2200.4}]
    out = formatting.format_player(players, "swiatek")
    assert "Iga Swiatek" in out
    assert "#1" in out
    assert "2200" in out


def test_format_player_multiple_lists_others():
    players = [
        {"name": "Alexander Zverev", "ranking": 4, "elo": 2000},
        {"name": "Mischa Zverev", "ranking": 900},
    ]
    out = formatting.format_player(players, "zverev")
    assert "Alexander Zverev" in out
    assert "Other matches" in out
    assert "Mischa Zverev" in out


def test_format_player_not_found():
    out = formatting.format_player([], "nobody")
    assert "No player found" in out
    assert "nobody" in out


def test_format_fixtures():
    fixtures = [
        {
            "players": {"p1": {"name": "A B"}, "p2": {"name": "C D"}},
            "tournament": "ATP Example Open",
            "start_time": "2026-08-21T10:00:00Z",
        }
    ]
    out = formatting.format_fixtures(fixtures)
    assert "A B" in out and "C D" in out
    assert "ATP Example Open" in out
    assert "2026-08-21T10:00:00Z" in out


def test_format_fixtures_empty():
    assert "No upcoming fixtures" in formatting.format_fixtures([])


def test_score_line_handles_dict_shape():
    # games as list of dicts instead of pairs
    score = {"games": [{"p1": 6, "p2": 3}], "points": {"p1": "40", "p2": "AD"}}
    line = formatting._score_line(score)
    assert "6-3" in line
    assert "40-AD" in line
