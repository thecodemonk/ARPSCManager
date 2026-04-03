# ARPSC Manager

A management platform for the **St. Clair County ARPSC** (Amateur Radio Public Service Corps). Built to track weather siren testing under the SKYWARN program and expanded to handle full organizational management: member profiles, event/attendance tracking, ICS-309 communications logs, training records, task book certification progress, and monthly state reporting.

Live at [sirens.sccarpsc.org](https://sirens.sccarpsc.org)

---

## Features

### Siren Testing
- Public dashboard showing all county sirens with pass/fail/overdue status
- Detailed siren pages with full test history grouped by year
- Volunteer signup for upcoming test dates (with optional reCAPTCHA)
- Admin test scheduling, assignment management, and result recording
- Test photos with auto-resize and thumbnails
- GPS coordinates with embedded satellite map view

### Member Management
- Member profiles with contact info, emergency contacts, and privacy settings
- Self-service member portal with email magic link authentication
- Admin can manage all member data for less tech-savvy members
- Configurable equipment types (HF, dual-band, digital/Winlink, backup power, etc.)
- Configurable training types with auto-computed expiration dates (e.g., SKYWARN every 2 years)
- Inactivity detection — flags members with no activity in 12+ months
- One-click "Add admin accounts as members" for bootstrapping

### Task Books
- Configurable certification levels with individual tasks
- CSV import for bulk task creation
- Per-member progress tracking with two officer sign-offs per task
- Progress visible to both members and admins

### Event & Attendance Tracking
- Event logging with categories (ARPSC, SKYWARN, Siren Test) and types (Meeting, Net, Training, Exercise, Deployment, etc.)
- Individual hours per member per event
- Siren tests auto-create events with attendance
- NTS liaison tracking for net events

### Monthly State Reporting
- Matches the Michigan ARES Event Log spreadsheet format
- Automatic categorization: Drills, Public Service Events, Public Safety Incidents, SKYWARN Activations
- Active member count, NTS liaison count, total person-hours
- Dollar value calculation ($34.79/hr, configurable)
- CSV export for state submission

### ICS-309 Communications Logs
- Digital ICS-309 form with all standard fields
- Inline entry management for radio traffic logging
- PDF generation matching the official ICS-309 format
- Optional linking to events for attendance integration

### Data Import/Export
- CSV export for all data: sirens, tests, assignments, schedules, members, training, equipment, events, attendance, comm logs, and configuration
- CSV import with preview and confirmation for sirens, tests, assignments, schedules, members, events, training, and attendance
- CSV formula injection protection on exports

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3 / Flask 3.1 |
| Database | SQLite (via Flask-SQLAlchemy) |
| Frontend | Bootstrap 5, vanilla JavaScript |
| Auth (Admin) | Google Workspace OAuth (Authlib) |
| Auth (Member) | Email magic link (itsdangerous + Gmail API) |
| Email | Gmail API with OAuth2 token |
| PDF | ReportLab |
| Image Processing | Pillow |
| Server | Gunicorn behind Nginx with Let's Encrypt SSL |
| Hosting | DigitalOcean (Ubuntu, 512MB droplet) |

---

## Project Structure

```
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── config.py            # Dev/Prod/Test config classes
│   ├── extensions.py        # Flask extensions init
│   ├── models.py            # All 17 database models
│   ├── filters.py           # Jinja template filters
│   ├── utils.py             # Status computation, photos, email, inactivity
│   ├── reports.py           # Monthly state report generation
│   ├── pdf.py               # ICS-309 PDF generation
│   ├── gmail.py             # Gmail API email sending
│   ├── auth/                # Google Workspace OAuth (admin login)
│   ├── public/              # Dashboard, siren detail, volunteer signup
│   ├── admin/               # All admin CRUD routes
│   ├── members/             # Member self-service + magic link auth
│   ├── static/              # CSS, JS, Bootstrap
│   └── templates/           # Jinja2 templates
├── deploy/
│   ├── sirentracker.service # systemd unit file
│   └── nginx-site.conf      # Nginx reverse proxy config
├── instance/                # SQLite DB + Gmail token (not in git)
├── media/photos/            # Test photos on disk (not in git)
├── migrations/              # Alembic database migrations
├── scripts/                 # Utilities (Gmail auth, backups, imports)
├── requirements.txt
├── wsgi.py                  # Gunicorn entry point
└── CLAUDE.md                # AI assistant instructions
```

---

## Setup

### Prerequisites
- Python 3.9+
- A Google Cloud project with OAuth 2.0 credentials (for admin login)
- A Gmail account with API access (for sending emails)

### Local Development

```bash
# Clone and set up virtual environment
git clone <repo-url>
cd ARPSCManager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values (see Environment Variables below)

# Initialize database
flask db upgrade

# Run development server
flask run --port 5001
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
SECRET_KEY=<random-string-at-least-32-chars>

# Google Workspace OAuth (admin login)
GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_WORKSPACE_DOMAIN=yourdomain.org

# Gmail API sender (for magic links and notifications)
GMAIL_SENDER=ARPSC Manager <noreply@yourdomain.org>

# Optional — reCAPTCHA for volunteer signup
RECAPTCHA_SITE_KEY=
RECAPTCHA_SECRET_KEY=
```

### Gmail API Setup

The app uses Gmail API to send magic link codes and admin notifications:

```bash
# Run locally to authorize (opens browser for Google sign-in)
python scripts/gmail_auth.py

# This creates instance/gmail_token.json
# Copy to server: scp instance/gmail_token.json server:/opt/sirentracker/instance/
```

---

## Production Deployment

### Server Setup

```bash
# On the server (Ubuntu)
sudo mkdir -p /opt/sirentracker
sudo chown www-data:www-data /opt/sirentracker
cd /opt/sirentracker

git clone <repo-url> .
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Create directories
mkdir -p instance media/photos
chown www-data:www-data instance media/photos

# Configure environment
cp .env.example .env
# Edit .env with production values

# Initialize database
sudo -u www-data .venv/bin/flask db upgrade

# Install systemd service
sudo cp deploy/sirentracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sirentracker
sudo systemctl start sirentracker

# Install Nginx config
sudo cp deploy/nginx-site.conf /etc/nginx/sites-available/sirentracker
sudo ln -s /etc/nginx/sites-available/sirentracker /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# SSL with Let's Encrypt
sudo certbot --nginx -d sirens.sccarpsc.org
```

### Deploying Updates

```bash
cd /opt/sirentracker && git pull
.venv/bin/pip install -r requirements.txt    # if deps changed
sudo -u www-data .venv/bin/flask db upgrade  # if migrations added
sudo systemctl restart sirentracker
```

---

## Authentication

The app uses two separate authentication systems:

### Admin (Google Workspace OAuth)
- Restricted to users with an email on the configured Google Workspace domain
- Provides access to all admin functionality: managing sirens, tests, members, events, comm logs, task books, reports, and configuration
- Login at `/auth/login`

### Member (Email Magic Link)
- Open to any email address
- Sends a 6-digit code + clickable link via Gmail API
- 10-minute expiry, 5 attempt limit, session regeneration on success
- Members can manage their own profile, equipment, training, and view activity
- Login at `/member/login`

Both auth systems coexist via Flask-Login with prefixed session IDs (`admin:N` / `member:N`).

---

## Siren Status Logic

Statuses are computed in priority order:

| Priority | Status | Condition |
|----------|--------|-----------|
| 1 | **Failed** | Tested this year and failed |
| 2 | **Passed** | Tested this year and passed |
| 3 | **Overdue** | No test in 12+ months or never tested |
| 4 | **Flagged** | Manually marked for recheck |
| 5 | **Assigned** | Volunteer claimed for upcoming test |
| 6 | **Untested** | Not yet tested this year (but tested within 12 months) |

---

## State Report Mapping

Events are mapped to Michigan ARES reporting categories:

| Event Type | State Report Category |
|---|---|
| Meeting, Net, Info Net, Simplex Net, Training, Exercise | Drills |
| Public Service Event, Siren Test | Public Service Events |
| Public Safety Incident, Deployment | Public Safety Incidents |
| SKYWARN Activation | SKYWARN Activations |
| General/Misc | Not reported to state |

**Total Public Safety** = Public Safety Incidents + SKYWARN Activations

---

## Backups

A weekly cron job runs `scripts/backup.sh` on the server:
- SQLite database dump
- CSV exports of all tables
- Test photos
- Uploaded to Google Drive

---

## License

Private — St. Clair County ARPSC.
