#!/usr/bin/env bash
# SirenTracker weekly backup — run via cron
# Snapshots the SQLite DB and photos, then uploads to Google Drive via
# rclone. The .backup file is comprehensive — there is no longer a
# per-table CSV export, since hand-maintained column lists drift out of
# date with the schema (and the admin UI exposes CSV export anyway).
#
# Cron example (every Sunday at 2 AM):
#   0 2 * * 0 /opt/sirentracker/scripts/backup.sh >> /var/log/sirentracker-backup.log 2>&1

set -euo pipefail

APP_DIR="/opt/sirentracker"
BACKUP_DIR="/tmp/sirentracker_backup_$(date +%Y%m%d)"
DB_PATH="${APP_DIR}/instance/sirentracker.db"
RCLONE_REMOTE="gdrive:SirenTracker-Backups"

echo "$(date '+%Y-%m-%d %H:%M:%S') Starting backup..."

mkdir -p "${BACKUP_DIR}"

# Safe SQLite backup (works while the app is running)
sqlite3 "${DB_PATH}" ".backup '${BACKUP_DIR}/sirentracker.db'"
echo "Snapshotted SQLite DB"

# NOTE: instance/gmail_token.json is intentionally NOT backed up — it is a
# long-lived Gmail send-as credential and uploading it to Drive would make
# the backup destination a credential exfil target. To rebuild after a
# disaster, re-run scripts/gmail_auth.py locally and scp the result.

# Photos
if [ -d "${APP_DIR}/media/photos" ]; then
    cp -r "${APP_DIR}/media/photos" "${BACKUP_DIR}/photos"
    echo "Copied photos directory"
fi

# Bus-factor README — instructions for non-technical recovery.
# Lives in the repo so it stays version-controlled; copied with a
# leading-underscore name so Drive lists it first.
README_SRC="${APP_DIR}/scripts/backup_README.txt"
if [ -f "${README_SRC}" ]; then
    cp "${README_SRC}" "${BACKUP_DIR}/README_FIRST.txt"
    echo "Copied recovery README"
else
    echo "WARN: ${README_SRC} not found — recovery README NOT included"
fi

# Upload to Google Drive — fail loudly if rclone returns non-zero so cron
# emails the failure and we don't silently delete a broken backup.
if ! rclone copy "${BACKUP_DIR}" "${RCLONE_REMOTE}/$(date +%Y-%m-%d)/" --config /root/.config/rclone/rclone.conf --log-level INFO; then
    echo "ERROR: rclone upload failed — leaving ${BACKUP_DIR} for inspection"
    exit 1
fi

# Cleanup
rm -rf "${BACKUP_DIR}"

echo "$(date '+%Y-%m-%d %H:%M:%S') Backup complete."
