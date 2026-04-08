from calendar import monthrange
from datetime import date
from flask import current_app
from sqlalchemy import func, extract

from .extensions import db
from .models import Event, EventAttendance, Member

# Maps local event types to state report categories
STATE_REPORT_MAPPING = {
    'Meeting': 'drills',
    'Net': 'drills',
    'Info Net': 'drills',
    'Simplex Net': 'drills',
    'Training': 'drills',
    'Exercise': 'drills',
    'Public Service Event': 'public_service',
    'Siren Test': 'public_service',
    'Public Safety Incident': 'public_safety',
    'Deployment': 'public_safety',
    'SKYWARN Activation': 'skywarn',
    # 'General/Misc' intentionally omitted — not reported to state
}


def generate_monthly_report(year, month):
    """Generate a monthly state report matching the ARES Event Log format."""
    events = Event.query.options(
        db.joinedload(Event.attendance)
    ).filter(
        extract('year', Event.date) == year,
        extract('month', Event.date) == month,
    ).order_by(Event.date).all()

    # Initialize counters
    categories = {
        'drills': {'count': 0, 'hours': 0.0},
        'public_service': {'count': 0, 'hours': 0.0},
        'public_safety': {'count': 0, 'hours': 0.0},
        'skywarn': {'count': 0, 'hours': 0.0},
    }

    total_person_hours = 0.0
    nets_with_nts_liaison = 0

    for event in events:
        # Get person-hours for this event
        event_person_hours = sum(a.hours for a in event.attendance)
        total_person_hours += event_person_hours

        # Count NTS liaison nets
        if event.has_nts_liaison and event.event_type in ('Net', 'Info Net', 'Simplex Net'):
            nets_with_nts_liaison += 1

        # Map to state category
        state_cat = STATE_REPORT_MAPPING.get(event.event_type)
        if state_cat:
            categories[state_cat]['count'] += 1
            categories[state_cat]['hours'] += event_person_hours

    # ARPSC member count, as-of end of the reporting month.
    # Skywarn-only spotters and siren-test-only volunteers are intentionally
    # excluded — only members the admin has flagged arpsc_active count for the
    # state. Historical reports stay accurate even after a member is later
    # archived or deactivated, because we filter on the audit dates.
    end_of_month = date(year, month, monthrange(year, month)[1])
    active_members = Member.query.filter(
        Member.arpsc_activated_at != None,  # noqa: E711 — SQLAlchemy IS NOT NULL
        Member.arpsc_activated_at <= end_of_month,
        db.or_(
            Member.arpsc_deactivated_at == None,  # noqa: E711
            Member.arpsc_deactivated_at > end_of_month,
        ),
        db.or_(
            Member.archived_at == None,  # noqa: E711
            Member.archived_at > end_of_month,
        ),
    ).count()

    # Dollar value
    dollar_rate = current_app.config.get('DOLLAR_VALUE_PER_HOUR', 34.79)
    dollar_value = total_person_hours * dollar_rate

    # Total public safety = public_safety + skywarn
    total_ps_count = categories['public_safety']['count'] + categories['skywarn']['count']
    total_ps_hours = categories['public_safety']['hours'] + categories['skywarn']['hours']

    return {
        'year': year,
        'month': month,
        'drills_count': categories['drills']['count'],
        'drills_hours': categories['drills']['hours'],
        'public_service_count': categories['public_service']['count'],
        'public_service_hours': categories['public_service']['hours'],
        'public_safety_count': categories['public_safety']['count'],
        'public_safety_hours': categories['public_safety']['hours'],
        'skywarn_count': categories['skywarn']['count'],
        'skywarn_hours': categories['skywarn']['hours'],
        'total_public_safety_count': total_ps_count,
        'total_public_safety_hours': total_ps_hours,
        'active_members': active_members,
        'nets_with_nts_liaison': nets_with_nts_liaison,
        'total_person_hours': total_person_hours,
        'dollar_value': dollar_value,
        'dollar_rate': dollar_rate,
        'events': events,
    }
