from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired

class LoginForm(FlaskForm):
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Einloggen')

class RegisterForm(FlaskForm):
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Registrieren')

class ReportForm(FlaskForm):
    latitude = StringField('Breitengrad', validators=[DataRequired()])
    longitude = StringField('Längengrad', validators=[DataRequired()])
    bundesland = StringField('Bundesland', validators=[DataRequired()])
    type = SelectField('Typ', choices=[('hornisse', 'Hornissensichtung'), ('nest', 'Nest')], validators=[DataRequired()])
    description = TextAreaField('Beschreibung', validators=[DataRequired()])
    photo = FileField('Foto', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Nur Bilder sind erlaubt!')
    ])
    submit = SubmitField('Meldung einreichen')

class MeldungForm(FlaskForm):
    latitude = StringField('Breitengrad', validators=[DataRequired()])
    longitude = StringField('Längengrad', validators=[DataRequired()])
    bundesland = StringField('Bundesland', validators=[DataRequired()])
    type = SelectField('Typ', choices=[('hornisse', 'Hornissensichtung'), ('nest', 'Nest')], validators=[DataRequired()])
    description = TextAreaField('Beschreibung', validators=[DataRequired()])
    photo = FileField('Foto', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Nur Bilder sind erlaubt!')
    ])
    submit = SubmitField('Speichern')
