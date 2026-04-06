# slacky

Slack from your terminal. Send messages, read channels, browse threads, and search — all from the CLI.

## Install

```bash
# From PyPI (coming soon)
uv tool install slacky

# From source
git clone https://github.com/asdf8601/slacky.git
cd slacky
uv tool install .
```

## Setup

Export your Slack bot token:

```bash
export SLACK_BOT_TOKEN=xoxb-your-bot-token
```

### Required Slack App Scopes

| Scope | Purpose |
|-------|---------|
| `chat:write` | Send messages |
| `channels:history` | Read messages in public channels |
| `groups:history` | Read messages in private channels |
| `im:history` | Read DMs |
| `channels:read` | List channels |
| `groups:read` | List private channels |
| `users:read` | Find users |
| `im:write` | Open DMs |
| `search:read` | Search messages (requires user token `xoxp-`) |

## Usage

### Send messages

```bash
slacky send '#general' 'Hello from the terminal!'
slacky send '@johndoe' 'Hey, quick question...'
slacky send '#general' 'Replying here' --thread 1234567890.123456
```

### Read messages

```bash
slacky read '#general'
slacky read '#general' --limit 50
slacky read '@johndoe'
```

### Read threads

```bash
# Using a Slack URL (copy from Slack)
slacky thread https://myteam.slack.com/archives/C123ABC/p1234567890123456

# Using channel + timestamp
slacky thread '#general' 1234567890.123456
```

### Search channels

```bash
slacky channels                  # list all
slacky channels deploy           # filter by name/topic/purpose
```

### Search messages

```bash
slacky search 'deployment failed'
slacky search 'in:#alerts from:@bot after:2024-01-01'
slacky search 'bug fix' --sort score --limit 10
```

### Find users

```bash
slacky users john
```

## Development

```bash
make dev       # install dependencies
make test      # run tests
make lint      # check formatting and linting
make format    # auto-format
```

## License

MIT
