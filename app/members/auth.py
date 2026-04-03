import hashlib
import secrets
from datetime import datetime, timezone

from flask import (
    current_app, flash, redirect, render_template, request,
    session, url_for,
)
from flask_login import login_user, logout_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from ..extensions import db, limiter
from ..gmail import send_email
from ..models import Member
from . import members_bp
from .forms import LoginForm, VerifyForm, RegisterForm


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


@members_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        # Generate 6-digit code and signed token
        code = f'{secrets.randbelow(1000000):06d}'
        s = _get_serializer()
        token = s.dumps(email, salt=current_app.config['MAGIC_LINK_SALT'])

        # Store hashed code in session
        session['magic_code_hash'] = hashlib.sha256(code.encode()).hexdigest()
        session['magic_email'] = email
        session['magic_time'] = datetime.now(timezone.utc).isoformat()

        # Send email
        verify_url = url_for('members.verify_token', token=token, _external=True)
        body = (
            f'Your ARPSC Manager login code is: {code}\n\n'
            f'Or click this link to log in:\n{verify_url}\n\n'
            f'This code expires in 10 minutes.'
        )
        try:
            send_email('ARPSC Manager Login Code', body, [email])
            flash('Check your email for a login code.', 'info')
        except Exception as e:
            current_app.logger.error(f'Failed to send magic link: {e}')
            flash('Failed to send login email. Please try again.', 'danger')
            return render_template('members/login.html', form=form)

        return redirect(url_for('members.verify'))

    return render_template('members/login.html', form=form)


@members_bp.route('/verify', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def verify():
    form = VerifyForm()
    if form.validate_on_submit():
        code = form.code.data.strip()
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        stored_hash = session.get('magic_code_hash')
        email = session.get('magic_email')
        magic_time = session.get('magic_time')

        if not stored_hash or not email or not magic_time:
            flash('Login session expired. Please try again.', 'warning')
            return redirect(url_for('members.login'))

        # Check expiry
        issued = datetime.fromisoformat(magic_time)
        elapsed = (datetime.now(timezone.utc) - issued).total_seconds()
        if elapsed > current_app.config['MAGIC_LINK_EXPIRY']:
            session.pop('magic_code_hash', None)
            session.pop('magic_email', None)
            session.pop('magic_time', None)
            flash('Code expired. Please request a new one.', 'warning')
            return redirect(url_for('members.login'))

        if code_hash != stored_hash:
            # Track failed attempts
            attempts = session.get('magic_attempts', 0) + 1
            session['magic_attempts'] = attempts
            if attempts >= 5:
                session.pop('magic_code_hash', None)
                session.pop('magic_email', None)
                session.pop('magic_time', None)
                session.pop('magic_attempts', None)
                flash('Too many failed attempts. Please request a new code.', 'danger')
                return redirect(url_for('members.login'))
            flash(f'Invalid code. {5 - attempts} attempts remaining.', 'danger')
            return render_template('members/verify.html', form=form)

        # Clear magic link session data
        session.pop('magic_code_hash', None)
        session.pop('magic_time', None)
        session.pop('magic_attempts', None)

        return _login_or_register(email)

    return render_template('members/verify.html', form=form)


@members_bp.route('/verify/<token>')
@limiter.limit("10/minute")
def verify_token(token):
    s = _get_serializer()
    try:
        email = s.loads(
            token,
            salt=current_app.config['MAGIC_LINK_SALT'],
            max_age=current_app.config['MAGIC_LINK_EXPIRY'],
        )
    except SignatureExpired:
        flash('Link expired. Please request a new one.', 'warning')
        return redirect(url_for('members.login'))
    except BadSignature:
        flash('Invalid link.', 'danger')
        return redirect(url_for('members.login'))

    # Clear any pending code session
    session.pop('magic_code_hash', None)
    session.pop('magic_time', None)
    session['magic_email'] = email

    return _login_or_register(email)


def _login_or_register(email):
    """Log in existing member or redirect to registration."""
    member = Member.query.filter(db.func.lower(Member.email) == email.lower()).first()
    if member:
        # Regenerate session to prevent fixation
        session.clear()
        login_user(member)
        flash(f'Welcome back, {member.name}!', 'success')
        return redirect(url_for('members.profile'))
    else:
        # Keep email in session for registration
        session['magic_email'] = email
        return redirect(url_for('members.register'))


@members_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def register():
    email = session.get('magic_email')
    if not email:
        flash('Please log in first to register.', 'warning')
        return redirect(url_for('members.login'))

    form = RegisterForm()
    if form.validate_on_submit():
        member = Member(
            name=form.name.data.strip(),
            callsign=form.callsign.data.strip() if form.callsign.data else None,
            email=email,
            phone=form.phone.data.strip() if form.phone.data else None,
            street=form.street.data.strip() if form.street.data else None,
            city=form.city.data.strip() if form.city.data else None,
            state=form.state.data.strip() if form.state.data else None,
            zip_code=form.zip_code.data.strip() if form.zip_code.data else None,
            country=form.country.data.strip() if form.country.data else 'US',
            emergency_contact=form.emergency_contact.data.strip() if form.emergency_contact.data else None,
            preferred_comm=form.preferred_comm.data,
            phone_privacy=form.phone_privacy.data,
            interest_skywarn=form.interest_skywarn.data,
            interest_ares_auxcomm=form.interest_ares_auxcomm.data,
        )
        db.session.add(member)
        db.session.commit()

        login_user(member)
        session.pop('magic_email', None)
        flash('Welcome! Your account has been created.', 'success')
        return redirect(url_for('members.profile'))

    return render_template('members/register.html', form=form, email=email)


@members_bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('public.dashboard'))
