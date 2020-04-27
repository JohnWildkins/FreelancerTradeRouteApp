from flask import Flask, render_template, request
from fltradeapp import get_data

app = Flask(__name__)

path_markets = 'market_commodities.ini' # paths to the data we need
distances_path = 'dump.csv'

distances, bases, comm_set, base_names = get_data(path_markets, distances_path)
bases_string = ' '.join([base[0] for base in base_names])
@app.route('/')
def dropdown():
    
    return bases_string


#@app.route('/', methods = ['GET'])
#@app.route('/score', methods=['POST'])



#if __name__ == '__main__':
#    app.run(port=5000, debug=True)