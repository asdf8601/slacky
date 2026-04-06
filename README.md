# slackli

Slack from your terminal. Send messages, read channels, browse threads, and search — all from the CLI.

## Install

```bash
uv tool install .
# or for development:
make dev
```

## Setup

Export your Slack token (bot or user token):

```bash
export SLACK_TOKEN=xoxb-your-bot-token
# or
export SLACK_TOKEN=xoxp-your-user-token
```

### Required Slack App Scopes

**Bot token** (`xoxb-`):
- `chat:write` — send messages
- `channels:history`, `groups:history`, `im:history` — read messages
- `channels:read`, `groups:read` — list channels
- `users:read` — find users
- `im:write` — open DMs

**User token** (`xoxp-`): additionally supports:
- `search:read` — search messages (requires user token)

## Usage

```bash
# Send a message to a channel
slackli send '#general' 'Hello from the terminal!'

# Send a DM to a user
slackli send '@johndoe' 'Hey, quick question...'

# Reply to a thread
slackli send '#general' 'Replying here' --thread 1234567890.123456

# Read messages from a channel
slackli read '#general'
slackli read '#general' --limit 50

# Read DMs with a user
slackli read '@johndoe'

# Read a thread
slackli thread '#general' 1234567890.123456

# List/search channels
slackli channels
slackli channels deploy

# Search messages across channels
slackli search 'deployment failed'
slackli search 'in:#alerts from:@bot after:2024-01-01'
slackli search 'bug fix' --sort score --limit 10

# Find users
slackli users john
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
