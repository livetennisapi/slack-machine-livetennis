import httpx
import respx

from machine.utils.collections import CaseInsensitiveDict

from sm_livetennis import formatting
from sm_livetennis.plugin import HELP_TEXT, NO_KEY_MESSAGE, LiveTennis

BASE = "https://api.livetennisapi.com/api/public/v1"


def make_plugin(with_key=True):
    settings = {}
    if with_key:
        settings["LIVETENNIS_API_KEY"] = "test-key"
    return LiveTennis(client=None, settings=CaseInsensitiveDict(settings), storage=None)


class FakeCommand:
    def __init__(self, text):
        self.text = text
        self.said = None

    async def say(self, text=None, ephemeral=True, **kwargs):
        self.said = text


class FakeMessage:
    def __init__(self):
        self.said = None

    async def say(self, text=None, **kwargs):
        self.said = text


async def test_help_when_empty():
    plugin = make_plugin()
    assert await plugin._handle("") == HELP_TEXT
    assert await plugin._handle("help") == HELP_TEXT


async def test_no_key_message():
    plugin = make_plugin(with_key=False)
    out = await plugin._handle("live")
    assert out == NO_KEY_MESSAGE
    assert "subscribe/free" in out


async def test_settings_key_is_case_insensitive():
    # Slack Machine settings are case-insensitive; env is SM_LIVETENNIS_API_KEY
    plugin = LiveTennis(
        client=None,
        settings=CaseInsensitiveDict({"livetennis_api_key": "abc"}),
        storage=None,
    )
    client = plugin._build_client()
    assert client is not None
    assert client.api_key == "abc"


@respx.mock
async def test_handle_live():
    respx.get(f"{BASE}/matches").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "players": {"p1": {"name": "Alcaraz"}, "p2": {"name": "Sinner"}},
                        "score": {"games": [[6, 4]], "points": ["30", "15"], "server": 1},
                    }
                ]
            },
        )
    )
    plugin = make_plugin()
    out = await plugin._handle("live")
    assert "Alcaraz" in out and "Sinner" in out
    assert "6-4" in out


@respx.mock
async def test_handle_rankings():
    respx.get(f"{BASE}/players").mock(
        return_value=httpx.Response(
            200, json={"data": [{"name": "Djokovic", "ranking": 1, "elo": 2100}]}
        )
    )
    plugin = make_plugin()
    out = await plugin._handle("rankings")
    assert "Djokovic" in out


@respx.mock
async def test_handle_player():
    respx.get(f"{BASE}/players").mock(
        return_value=httpx.Response(
            200, json={"data": [{"name": "Coco Gauff", "ranking": 3, "elo": 2050}]}
        )
    )
    plugin = make_plugin()
    out = await plugin._handle("player gauff")
    assert "Coco Gauff" in out
    assert "#3" in out


async def test_handle_player_missing_name():
    plugin = make_plugin()
    out = await plugin._handle("player")
    assert "Usage" in out


@respx.mock
async def test_handle_fixtures():
    respx.get(f"{BASE}/fixtures").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"players": {"p1": {"name": "A"}, "p2": {"name": "B"}}}]},
        )
    )
    plugin = make_plugin()
    out = await plugin._handle("next")
    assert "Upcoming fixtures" in out


async def test_handle_unknown_subcommand():
    plugin = make_plugin()
    out = await plugin._handle("frobnicate")
    assert "Unknown subcommand" in out


@respx.mock
async def test_handle_auth_error_message():
    respx.get(f"{BASE}/matches").mock(return_value=httpx.Response(401))
    plugin = make_plugin()
    out = await plugin._handle("live")
    assert "rejected" in out.lower()


@respx.mock
async def test_handle_rate_limit_message():
    respx.get(f"{BASE}/matches").mock(return_value=httpx.Response(429))
    plugin = make_plugin()
    out = await plugin._handle("live")
    assert "Rate limit" in out


@respx.mock
async def test_handle_api_error_message():
    respx.get(f"{BASE}/matches").mock(return_value=httpx.Response(503))
    plugin = make_plugin()
    out = await plugin._handle("live")
    assert "unavailable" in out.lower()


@respx.mock
async def test_command_handler_calls_say():
    respx.get(f"{BASE}/matches").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    plugin = make_plugin()
    cmd = FakeCommand("live")

    class FakeLogger:
        def info(self, *a, **k):
            pass

    await plugin.tennis_command(cmd, FakeLogger())
    assert cmd.said is not None
    assert "No live matches" in cmd.said


async def test_mention_handler_calls_say():
    plugin = make_plugin(with_key=False)
    msg = FakeMessage()
    await plugin.tennis_mention(msg, query="live", logger=None)
    assert msg.said == NO_KEY_MESSAGE


def test_no_gambling_language_in_module():
    import inspect

    import sm_livetennis.client as client_mod
    import sm_livetennis.formatting as fmt_mod
    import sm_livetennis.plugin as plugin_mod

    banned = ("bet", "betting", "gambl", "casino", "wager", "odds", "bookmaker")
    for mod in (client_mod, fmt_mod, plugin_mod):
        src = inspect.getsource(mod).lower()
        for word in banned:
            assert word not in src, f"banned term {word!r} in {mod.__name__}"


def test_help_text_has_vendor_disclosure():
    assert "livetennisapi.com" in HELP_TEXT
    assert "subscribe/free" in NO_KEY_MESSAGE
    # formatting module surfaces the tennis marker constant
    assert formatting.TENNIS == ":tennis:"
