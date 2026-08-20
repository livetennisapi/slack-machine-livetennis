# slack-machine-livetennis

Live tennis **scores, rankings and fixtures** inside Slack — a plugin for
[Slack Machine](https://github.com/DonDebonair/slack-machine).

> **Data source disclosure:** this plugin is built and maintained by the
> **[Live Tennis API](https://livetennisapi.com)** team and talks to the Live
> Tennis API. A **free key** (live scores, match state, players with ranking &
> Elo, fixtures — 30 req/min, 100/day, **no card required**) is available at
> <https://livetennisapi.com/subscribe/free>.

## Features

- `/tennis live` — matches in progress right now, with score, who's serving,
  and break-point / retirement / walkover flags
- `/tennis rankings` — top ranked players, with Elo
- `/tennis player <name>` — a player's ranking and Elo
- `/tennis next` — upcoming fixtures
- Natural language: mention the bot with `tennis live`, `tennis player alcaraz`, …
- Graceful handling of a missing key, a rejected key (401), rate limits (429),
  and empty results

## Install

Using `uv`:

```bash
uv add slack-machine-livetennis
```

Using `pip` (add to your bot's `requirements.txt`):

```
slack-machine-livetennis
```

## Configure

Add the plugin to the `PLUGINS` list in your bot's `local_settings.py`, and
provide your Live Tennis API key as the `LIVETENNIS_API_KEY` setting:

```python
PLUGINS = [
    "machine.plugins.builtin.general.HelloPlugin",
    "machine.plugins.builtin.help.HelpPlugin",
    "sm_livetennis.LiveTennis",
]

SLACK_APP_TOKEN = "xapp-..."
SLACK_BOT_TOKEN = "xoxb-..."

# Get a free key at https://livetennisapi.com/subscribe/free
LIVETENNIS_API_KEY = "your-key-here"
```

Settings can also come from the environment using Slack Machine's `SM_` prefix
convention, so the following is equivalent to the setting above:

```bash
export SM_LIVETENNIS_API_KEY="your-key-here"
```

You need a Slack app configured with a slash command `/tennis` pointing at your
bot (Socket Mode), plus the usual Slack Machine bot scopes. See the
[Slack Machine docs](https://dondebonair.github.io/slack-machine/) for setup.

### Optional settings

| Setting | Default | Purpose |
| --- | --- | --- |
| `LIVETENNIS_API_KEY` | _(required at runtime)_ | Your Live Tennis API key |
| `LIVETENNIS_BASE_URL` | `https://api.livetennisapi.com/api/public/v1` | Override the API base URL |

## Usage

```
/tennis live
/tennis rankings
/tennis player alcaraz
/tennis next
/tennis help
```

Or mention the bot:

```
@yourbot tennis live
@yourbot tennis player sinner
```

## Development

```bash
uv sync            # or: pip install -e ".[test]"
pytest             # unit tests, fully mocked — no network
```

Tests mock all HTTP with [`respx`](https://lundberg.github.io/respx/) and never
hit the network.

## License

[MIT](LICENSE)
