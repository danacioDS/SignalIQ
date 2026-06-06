#!/usr/bin/env bash
set -euo pipefail

CRON_FILE="/tmp/signaliq_cron"
CRONTAB=$(mktemp)

crontab -l > "$CRONTAB" 2>/dev/null || true

PRICES_ENTRY="5 20 * * * cd /opt/signaliq && /usr/bin/python3 -m layer1.orchestrator --type prices"
NEWS_ENTRY="0 6,12,18 * * * cd /opt/signaliq && /usr/bin/python3 -m layer1.orchestrator --type news"

mkdir -p ~/logs/signaliq

for entry in "$PRICES_ENTRY" "$NEWS_ENTRY"; do
    if ! grep -qF "$entry" "$CRONTAB"; then
        echo "$entry" >> "$CRONTAB"
    fi
done

crontab "$CRONTAB"
rm "$CRONTAB"

echo "Crontab installed. Current entries:"
crontab -l
