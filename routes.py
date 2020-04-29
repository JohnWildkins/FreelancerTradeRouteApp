from flask import Flask, render_template, request

from trade_sorts import get_data
from config import Config

app=Flask(__name__)
app.config.from_object(Config)

from app import routes

path_markets = 'market_commodities.ini' # paths to the data we need
distances_path = 'dump.csv'

# declare a bunch of variables
distances, bases, comm_set, base_names = get_data(path_markets, distances_path)
bases_string = ' '.join([base[0] for base in base_names])
base_names_list = [base[0] for base in base_names]
sys = "name does not exit"




@app.route('/')
def dropdown():

    return render_template('base_dropdown.html', drops = base_names_list, commodities = comm_set)

if __name__ == '__main__':
    app.run()
#@app.route('/', methods = ['GET'])
#@app.route('/score', methods=['POST'])



#if __name__ == '__main__':
#    app.run(port=5000, debug=True)
