#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="logs"
RETENTION_DAYS=90

if [ -d "$LOG_DIR" ]; then
    for logfile in "$LOG_DIR"/ingestion.log; do
        if [ -f "$logfile" ]; then
            timestamp=$(date +%Y%m%d_%H%M%S)
            mv "$logfile" "${logfile}-${timestamp}"
        fi
    done

    find "$LOG_DIR" -name "ingestion.log-*" -mtime +$RETENTION_DAYS -delete
fi
