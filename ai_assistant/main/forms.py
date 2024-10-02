from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Optional
#import json

class PreferencesForm(FlaskForm):
    role = StringField('Job Title', validators=[DataRequired()])
    assistant_personality = TextAreaField("AI Assistant's Personality", validators=[Optional()])
    about_me = TextAreaField('About Me', validators=[Optional()])
    submit = SubmitField('Save Preferences')

    """
    preferences = TextAreaField('Your Preferences (in JSON format)', validators=[DataRequired()])

    submit = SubmitField('Save Preferences')

    def validate_preferences(self, field):
        try:
            json.loads(field.data)
        except json.JSONDecodeError:
            raise ValidationError('Preferences must be valid JSON.')
    """
