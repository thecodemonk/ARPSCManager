#!/usr/bin/env bash
# SirenTracker weekly backup — run via cron
# Copies SQLite DB and exports CSVs, then uploads to Google Drive via rclone
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

# Safe SQLite backup
sqlite3 "${DB_PATH}" ".backup '${BACKUP_DIR}/sirentracker.db'"

# CSV exports
cd "${APP_DIR}"
source .venv/bin/activate
FLASK_APP=wsgi.py python -c "
from app import create_app
from app.models import Siren, Test, Assignment, TestSchedule
import csv, io

app = create_app('production')
with app.app_context():
    for name, model, cols in [
        ('sirens', Siren, ['siren_id','name','location_text','location_url','year_in_service','siren_type','active','needs_retest']),
        ('tests', Test, ['id','siren_id','test_date','observer','sound_ok','rotation_ok','vegetation_damage_ok','notes']),
        ('assignments', Assignment, ['id','siren_id','volunteer_name','test_date','status']),
        ('schedules', TestSchedule, ['id','test_date','test_time','description']),
    ]:
        with open('${BACKUP_DIR}/' + name + '.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for row in model.query.all():
                w.writerow({c: getattr(row, c) for c in cols})
        print(f'Exported {name}.csv')
"

# Upload to Google Drive
rclone copy "${BACKUP_DIR}" "${RCLONE_REMOTE}/$(date +%Y-%m-%d)/" --log-level INFO

# Cleanup
rm -rf "${BACKUP_DIR}"

echo "$(date '+%Y-%m-%d %H:%M:%S') Backup complete."
