#!/usr/bin/env python3
"""Generate first-Monday test dates for a given year and insert into the database."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import TestSchedule
from app.utils import generate_first_mondays


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    app = create_app()
    with app.app_context():
        dates = generate_first_mondays(year)
        added = 0
        for d in dates:
            if not TestSchedule.query.filter_by(test_date=d).first():
                db.session.add(TestSchedule(test_date=d, test_time='13:00', description='Monthly Test'))
                added += 1
        db.session.commit()
        print(f'Added {added} test dates for {year}.')


if __name__ == '__main__':
    main()
