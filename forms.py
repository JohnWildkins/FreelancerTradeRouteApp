from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, SubmitField, validators

class BaseList(FlaskForm):
    base_field = SelectField('Base')
    submit = SubmitField()

class CommodList(FlaskForm):
    commod_field = SelectField('Commodity')
    submit = SubmitField()