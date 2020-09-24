from flask import Flask, render_template, request, jsonify

from trade_sorts import get_data
from config import Config
import forms, os, time

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
commod_names_list = [(commod_int, "{0} ({1})".format(commod_name['display_name'], commod_int)) for commod_int, commod_name in commodities.items() if commodities[commod_int]['produced_by']]

#TEST PLEASE IGNORE
# print(distances)
# mask = distances.loc[(distances['start'] == 'li01_01_base') & (distances['end'] == 'li02_05_base')]
# print(mask['time'].values[0])

def ms_to_hms(duration):
    minutes, seconds = divmod(duration / 1000, 60)
    return "{0:d} min {1:d} sec".format(int(minutes), int(seconds))

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
    form.commo.choices = sorted(commod_names_list)
    if request.method == 'POST':
        commo = request.form['commo']
        if commo:
            producers_r = commodities[commo]['produced_by']
            consumers_r = commodities[commo]['consumed_by']
            trade_map = dict()
            # producer / consumer map time. wake me up inside.

            for producer in producers_r:
                pn = producer['nickname']
                trade_map[pn] = dict()
                for consumer in consumers_r:
                    # AIN'T NO PARTY LIKE A O(N^2) PARTY
                    # CAUSE A O(N^2) PARTY EATS THE CPU ALIVE
                    cn = consumer['nickname']
                    if pn == cn:
                        continue
                    try:
                        mask = distances.loc[pn, cn]
                    except KeyError as e:
                        # print("No base found in travel time doc: {0}".format(e.args[0]))
                        continue
                    try:
                        trade_map[pn]['name'] = producer['display_name']
                        trade_map[pn][cn] = {
                            'name': consumer['display_name'],
                            'time': ms_to_hms(int(mask.values[0]))
                        }
                    except IndexError:
                        trade_map[pn][cn] = -1

            market = {
                'producers': {
                    p['display_name']: {
                        'system': p['system_dis'],
                        'price': p['commodities'][commo]['actual_price']
                    } for p in producers_r
                },
                'consumers': {
                    c['display_name']: {
                        'system': c['system_dis'],
                        'price': c['commodities'][commo]['actual_price']
                    } for c in consumers_r
                },
                'trade_map': trade_map
            }
            return jsonify({'market': market, 'commo': commo})
        else:
            return jsonify({'error': 'No data received by AJAX call!'})
    return render_template('commod_dropdown.html', form=form)

# @app.route('/commodity/<commo>', methods=['GET'])
# def commod_inspect(commo):

if __name__ == '__main__':
    app.run(debug=True)
#@app.route('/', methods = ['GET'])
#@app.route('/score', methods=['POST'])



#if __name__ == '__main__':
#    app.run(port=5000, debug=True)
