import csv
import io
import os
import tempfile
from datetime import date, datetime

from flask import (
    abort, render_template, request, flash, redirect, url_for,
    Response, stream_with_context, session,
)
from .decorators import admin_required
from .forms import SirenForm, TestForm
from . import admin_bp
from ..extensions import db
from ..models import Siren, Test, Assignment, TestSchedule, AdminUser
from ..utils import generate_first_mondays


# --- Sirens ---

@admin_bp.route('/')
@admin_bp.route('/sirens')
@admin_required
def sirens():
    all_sirens = Siren.query.order_by(Siren.siren_id).all()
    return render_template('admin/sirens.html', sirens=all_sirens)


@admin_bp.route('/sirens/add', methods=['GET', 'POST'])
@admin_required
def siren_add():
    form = SirenForm()
    if form.validate_on_submit():
        siren = Siren(
            siren_id=form.siren_id.data.strip(),
            name=form.name.data.strip(),
            location_text=form.location_text.data.strip() if form.location_text.data else None,
            location_url=form.location_url.data.strip() if form.location_url.data else None,
            year_in_service=form.year_in_service.data.strip() if form.year_in_service.data else None,
            siren_type=form.siren_type.data,
            active=form.active.data,
            needs_retest=form.needs_retest.data,
        )
        db.session.add(siren)
        db.session.commit()
        flash(f'Siren {siren.siren_id} added.', 'success')
        return redirect(url_for('admin.sirens'))
    return render_template('admin/siren_form.html', form=form, siren=None)


@admin_bp.route('/sirens/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def siren_edit(id):
    siren = db.session.get(Siren, id) or abort(404)
    form = SirenForm(obj=siren)
    if form.validate_on_submit():
        form.populate_obj(siren)
        db.session.commit()
        flash(f'Siren {siren.siren_id} updated.', 'success')
        return redirect(url_for('admin.sirens'))
    return render_template('admin/siren_form.html', form=form, siren=siren)


# --- Tests ---

@admin_bp.route('/tests')
@admin_required
def tests():
    all_tests = (
        Test.query
        .join(Siren)
        .order_by(Test.test_date.desc())
        .all()
    )
    return render_template('admin/tests.html', tests=all_tests)


@admin_bp.route('/tests/add', methods=['GET', 'POST'])
@admin_required
def test_add():
    form = TestForm()
    active_sirens = Siren.query.filter_by(active=True).order_by(Siren.siren_id).all()
    form.siren_id.choices = [
        (s.id, f'{s.siren_id} — {s.name}')
        for s in active_sirens
    ]
    # Store siren types for JS conditional rotation field
    siren_types = {s.id: s.siren_type for s in active_sirens}

    # Pre-fill from query params (e.g. coming from assignment "Log Result")
    assignment_id = request.args.get('assignment', type=int)
    if request.method == 'GET':
        if request.args.get('siren'):
            form.siren_id.data = request.args.get('siren', type=int)
        if request.args.get('date'):
            form.test_date.data = date.fromisoformat(request.args['date'])
        if request.args.get('observer'):
            form.observer.data = request.args['observer']

    if form.validate_on_submit():
        siren = db.session.get(Siren, form.siren_id.data)
        rotation_ok = form.rotation_ok.data if siren.siren_type == 'ROTATE' else None

        test = Test(
            siren_id=form.siren_id.data,
            test_date=form.test_date.data,
            observer=form.observer.data.strip(),
            passed=form.passed.data,
            sound_ok=form.sound_ok.data,
            rotation_ok=rotation_ok,
            vegetation_damage_ok=form.vegetation_damage_ok.data,
            notes=form.notes.data.strip() if form.notes.data else None,
        )
        db.session.add(test)

        # Auto-clear needs_retest on pass
        if test.passed and siren.needs_retest:
            siren.needs_retest = False

        # Auto-complete the linked assignment, or find a matching one
        linked = db.session.get(Assignment, assignment_id) if assignment_id else None
        if linked and linked.status == 'CLAIMED':
            linked.status = 'COMPLETED'
        else:
            matching = Assignment.query.filter_by(
                siren_id=siren.id,
                test_date=test.test_date,
                status='CLAIMED',
            ).first()
            if matching:
                matching.status = 'COMPLETED'

        db.session.commit()
        flash('Test result recorded.', 'success')
        if assignment_id:
            return redirect(url_for('admin.assignments'))
        return redirect(url_for('admin.tests'))

    return render_template('admin/test_form.html', form=form, siren_types=siren_types)


# --- Assignments ---

@admin_bp.route('/assignments')
@admin_required
def assignments():
    all_assignments = (
        Assignment.query
        .join(Siren)
        .order_by(Assignment.test_date.desc())
        .all()
    )
    return render_template('admin/assignments.html', assignments=all_assignments)


@admin_bp.route('/assignments/<int:id>/action', methods=['POST'])
@admin_required
def assignment_action(id):
    assignment = db.session.get(Assignment, id) or abort(404)
    action = request.form.get('action')
    if action == 'complete':
        assignment.status = 'COMPLETED'
        flash('Assignment marked as completed.', 'success')
    elif action == 'release':
        assignment.status = 'RELEASED'
        flash('Assignment released.', 'info')
    db.session.commit()
    return redirect(url_for('admin.assignments'))


# --- Schedule ---

@admin_bp.route('/schedule')
@admin_required
def schedule():
    schedules = TestSchedule.query.order_by(TestSchedule.test_date).all()
    return render_template('admin/schedule.html',
                           schedules=schedules,
                           current_year=date.today().year)


@admin_bp.route('/schedule/generate', methods=['POST'])
@admin_required
def schedule_generate():
    year = request.form.get('year', date.today().year, type=int)
    dates = generate_first_mondays(year)
    added = 0
    for d in dates:
        existing = TestSchedule.query.filter_by(test_date=d).first()
        if not existing:
            db.session.add(TestSchedule(test_date=d, test_time='13:00', description='Monthly Test'))
            added += 1
    db.session.commit()
    flash(f'Generated {added} new monthly test dates for {year}.', 'success')
    return redirect(url_for('admin.schedule'))


@admin_bp.route('/schedule/add', methods=['POST'])
@admin_required
def schedule_add():
    test_date_str = request.form.get('test_date')
    test_time = request.form.get('test_time', '13:00')
    description = request.form.get('description', 'Special Test')
    try:
        test_date_val = date.fromisoformat(test_date_str)
    except (ValueError, TypeError):
        flash('Invalid date.', 'danger')
        return redirect(url_for('admin.schedule'))

    db.session.add(TestSchedule(
        test_date=test_date_val,
        test_time=test_time,
        description=description,
    ))
    db.session.commit()
    flash('Test date added.', 'success')
    return redirect(url_for('admin.schedule'))


@admin_bp.route('/schedule/<int:id>/delete', methods=['POST'])
@admin_required
def schedule_delete(id):
    entry = db.session.get(TestSchedule, id) or abort(404)
    db.session.delete(entry)
    db.session.commit()
    flash('Test date removed.', 'info')
    return redirect(url_for('admin.schedule'))


# --- CSV Export ---

@admin_bp.route('/export/<table>')
@admin_required
def export_csv(table):
    if table == 'sirens':
        columns = ['siren_id', 'name', 'location_text', 'location_url',
                    'year_in_service', 'siren_type', 'active', 'needs_retest']
        rows = Siren.query.order_by(Siren.siren_id).all()
    elif table == 'tests':
        columns = ['siren_id', 'test_date', 'observer', 'passed',
                    'sound_ok', 'rotation_ok', 'vegetation_damage_ok', 'notes']
        rows = Test.query.join(Siren).order_by(Test.test_date.desc()).all()
        # Replace FK with siren external ID
        def row_dict(t):
            d = {c: getattr(t, c) for c in columns}
            d['siren_id'] = t.siren.siren_id
            return d
    elif table == 'assignments':
        columns = ['siren_id', 'volunteer_name', 'test_date', 'status']
        rows = Assignment.query.join(Siren).order_by(Assignment.test_date.desc()).all()
        def row_dict(a):
            d = {c: getattr(a, c) for c in columns}
            d['siren_id'] = a.siren.siren_id
            return d
    elif table == 'schedules':
        columns = ['test_date', 'test_time', 'description']
        rows = TestSchedule.query.order_by(TestSchedule.test_date).all()
    else:
        flash('Unknown table.', 'danger')
        return redirect(url_for('admin.import_export'))

    def generate():
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        for row in rows:
            if table in ('tests', 'assignments'):
                writer.writerow(row_dict(row))
            else:
                writer.writerow({c: getattr(row, c) for c in columns})
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    filename = f'sirentracker_{table}_{date.today().isoformat()}.csv'
    return Response(
        stream_with_context(generate()),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )


# --- CSV Import ---

@admin_bp.route('/import-export')
@admin_required
def import_export():
    return render_template('admin/import_export.html',
                           preview_rows=None, preview_cols=None, import_id=None)


@admin_bp.route('/import', methods=['POST'])
@admin_required
def import_csv():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        flash('Please upload a CSV file.', 'danger')
        return redirect(url_for('admin.import_export'))

    content = file.stream.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    if not rows:
        flash('CSV file is empty.', 'warning')
        return redirect(url_for('admin.import_export'))

    # Store in temp file for confirm step
    import_id = datetime.now().strftime('%Y%m%d%H%M%S')
    tmp_path = os.path.join(tempfile.gettempdir(), f'sirentracker_import_{import_id}.csv')
    with open(tmp_path, 'w', newline='') as f:
        f.write(content)

    session['import_path'] = tmp_path

    return render_template('admin/import_export.html',
                           preview_rows=rows[:50],
                           preview_cols=reader.fieldnames,
                           import_id=import_id)


@admin_bp.route('/import/confirm', methods=['POST'])
@admin_required
def import_confirm():
    tmp_path = session.pop('import_path', None)
    if not tmp_path or not os.path.exists(tmp_path):
        flash('Import session expired. Please upload again.', 'warning')
        return redirect(url_for('admin.import_export'))

    with open(tmp_path, 'r') as f:
        reader = csv.DictReader(f)
        added = 0
        updated = 0
        for row in reader:
            ext_id = row.get('siren_id', '').strip()
            if not ext_id:
                continue
            existing = Siren.query.filter_by(siren_id=ext_id).first()
            if existing:
                existing.name = row.get('name', existing.name).strip()
                existing.location_text = row.get('location_text', existing.location_text)
                existing.location_url = row.get('location_url', existing.location_url)
                existing.year_in_service = row.get('year_in_service', existing.year_in_service)
                existing.siren_type = row.get('siren_type', existing.siren_type) or 'FIXED'
                updated += 1
            else:
                siren = Siren(
                    siren_id=ext_id,
                    name=row.get('name', ext_id).strip(),
                    location_text=row.get('location_text'),
                    location_url=row.get('location_url'),
                    year_in_service=row.get('year_in_service'),
                    siren_type=row.get('siren_type', 'FIXED') or 'FIXED',
                )
                db.session.add(siren)
                added += 1
        db.session.commit()

    os.unlink(tmp_path)
    flash(f'Import complete: {added} added, {updated} updated.', 'success')
    return redirect(url_for('admin.import_export'))
