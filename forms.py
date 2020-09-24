from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, SubmitField, validators

class BaseList(FlaskForm):
    base_field = SelectField('Base')
    submit = SubmitField()

class CommodList(FlaskForm):
    commo = SelectField('Commodity')
    submit = SubmitField()