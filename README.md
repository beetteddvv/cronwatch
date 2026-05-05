# cronwatch

Lightweight daemon that monitors cron job execution and sends alerts on failures or missed runs.

## Installation

```bash
pip install cronwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/cronwatch.git && cd cronwatch && pip install .
```

## Usage

Define your monitored jobs in `cronwatch.yaml`:

```yaml
jobs:
  backup-db:
    schedule: "0 2 * * *"
    timeout: 300
    alert: email
  sync-files:
    schedule: "*/15 * * * *"
    timeout: 60
    alert: slack
```

Start the daemon:

```bash
cronwatch start --config cronwatch.yaml
```

Wrap your cron command to report execution status:

```bash
# In your crontab
0 2 * * * cronwatch run backup-db -- /usr/local/bin/backup.sh
```

Check status of monitored jobs:

```bash
cronwatch status
```

cronwatch will send alerts if a job fails (non-zero exit code), exceeds its timeout, or does not run within the expected schedule window.

## Configuration

| Key | Description |
|---|---|
| `schedule` | Cron expression defining expected run frequency |
| `timeout` | Max allowed runtime in seconds |
| `alert` | Alert channel (`email`, `slack`, `webhook`) |

## License

MIT