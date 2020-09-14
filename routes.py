from flask import Flask, render_template, request

from trade_sorts import get_data
from config import Config

app=Flask(__name__)
app.config.from_object(Config)

# declare a bunch of variables
distances, bases, comm_set, base_names, sys_names, commod_names = get_data(Config.MARKET_PATH, Config.DISTANCE_PATH)
base_names_list = ["{0} ({1})".format(base_name, base_int) for base_int, base_name in base_names.items()]
commod_names_list = ["{0} ({1})".format(commod_name, commod_int) for commod_int, commod_name in commod_names.items()]
sys = "name does not exit"

@app.route('/')
def dropdown():

    return render_template('base_dropdown.html', drops = base_names_list, commodities = commod_names_list)

if __name__ == '__main__':
    app.run()
#@app.route('/', methods = ['GET'])
#@app.route('/score', methods=['POST'])



#if __name__ == '__main__':
#    app.run(port=5000, debug=True)
