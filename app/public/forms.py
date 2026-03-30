from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length


class SignupForm(FlaskForm):
    volunteer_name = StringField('Name / Callsign', validators=[DataRequired(), Length(max=100)])
    siren_id = SelectField('Siren', coerce=int, validators=[DataRequired()])
    test_date = SelectField('Test Date', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Length(max=500)])
    # Honeypot field — should be left empty by humans
    website = HiddenField()
