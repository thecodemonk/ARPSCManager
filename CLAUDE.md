# SirenTracker

Weather siren testing tracker for St. Clair County ARPSC (Amateur Radio Public Service Corps).

## Stack
- Python Flask + SQLite + Bootstrap 5
- Gunicorn (2 workers, port 8100) behind Nginx with SSL
- Google Workspace OAuth for admin login
- Gmail API for email notifications (sends as noreply@sccarpsc.org)
- Deployed at sirens.sccarpsc.org on Ubuntu (DigitalOcean 512MB droplet)

## Project Structure
- `app/` — Flask application (factory pattern via `create_app()`)
  - `public/` — Dashboard, siren detail, volunteer signup (no auth)
  - `admin/` — Siren/test/assignment management (Google OAuth required)
  - `auth/` — Google Workspace OAuth login
  - `models.py` — Siren, Test, Assignment, TestSchedule, AdminUser
  - `gmail.py` — Gmail API send (OAuth token in `instance/gmail_token.json`)
  - `utils.py` — Status computation, photo processing, email notifications
- `media/photos/` — Test photos on disk (not in git)
- `instance/` — SQLite DB and Gmail token (not in git)
- `deploy/` — systemd service and nginx config
- `scripts/` — Auth, backup, import utilities

## Key Commands
```bash
# Local dev
flask run

# Database migrations
flask db migrate -m "description"
flask db upgrade

# Gmail auth (run locally, copy token to server)
python scripts/gmail_auth.py

# Backup (runs via cron on server)
/opt/sirentracker/scripts/backup.sh
```

## Server Deployment
```bash
cd /opt/sirentracker && git pull
.venv/bin/pip install -r requirements.txt  # if deps changed
sudo -u www-data .venv/bin/flask db upgrade  # if migrations
sudo systemctl restart sirentracker
```

## Siren Statuses (priority order)
1. **Failed** — tested this year and failed
2. **Passed** — tested this year and passed
3. **Overdue** — no test in over 12 months or never tested
4. **Flagged** — manually marked for recheck (needs_retest)
5. **Assigned** — volunteer claimed for upcoming test
6. **Untested** — not yet tested this year (but tested within 12 months)

## Notes
- Static CSS has cache-busting `?v=N` in base.html — bump when changing styles
- Photos auto-resized to max 1200px, thumbnails at 200px, JPEG format
- `instance/` and `media/photos/` must be writable by www-data on server
- reCAPTCHA on volunteer signup (optional, needs keys in .env)
- Backups run weekly via cron: SQLite + CSV exports + photos to Google Drive
