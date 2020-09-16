from flask import Flask, render_template, request

from trade_sorts import get_data
from config import Config
import forms, os

app=Flask(__name__)
app.config.from_object(Config)

try:
    with open('ftra_secretkey', 'r') as s:
        app.secret_key = s.read()
except IOError:
    with open('ftra_secretkey', 'w') as s:
        app.secret_key = os.urandom(16)
        print(app.secret_key, file=s)

# declare a bunch of variables
distances, bases, commodities = get_data(Config.MARKET_PATH, Config.DISTANCE_PATH)
base_names_list = [(base_int, "{0} ({1})".format(base_name['display_name'], base_int)) for base_int, base_name in bases.items()]
commod_names_list = [(commod_int, "{0} ({1})".format(commod_name['display_name'], commod_int)) for commod_int, commod_name in commodities.items()]

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/base', methods=['GET', 'POST'])
def base_dropdown():
    form = forms.BaseList()
    form.base_field.choices = base_names_list
    if form.is_submitted():
        try:
            commods = bases[form.base_field.data]
        except KeyError:
            commods = {"ERROR": "No commodities found on base '{0}'".format(form.base_field.data)}
        return render_template('base_dropdown.html', form=form, commods=commods)
    else:
        return render_template('base_dropdown.html', form=form)

@app.route('/commodity', methods=['GET', 'POST'])
def commod_dropdown():
    form = forms.CommodList()
    form.commod_field.choices = sorted(commod_names_list)
    if form.is_submitted():
        try:
            producers = commodities[form.commod_field.data]['produced_by']
            consumers = commodities[form.commod_field.data]['consumed_by']
        except KeyError:
            producers, consumers = [], []
        return render_template('commod_dropdown.html', form=form, producers=producers, consumers=consumers, commod = form.commod_field.data)
    return render_template('commod_dropdown.html', form=form)

if __name__ == '__main__':
    app.run()
#@app.route('/', methods = ['GET'])
#@app.route('/score', methods=['POST'])



#if __name__ == '__main__':
#    app.run(port=5000, debug=True)
