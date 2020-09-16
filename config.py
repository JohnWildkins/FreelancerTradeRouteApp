import os

class Base(object):
     commod_list = [] #to be iteratively filled with all the commodities the base handles

class Config(object):
    FILEPATH = os.getcwd() + '/' # TODO: handling for this program being run from outside the FL directory
    DATAPATH = FILEPATH + 'DATA/'
    UNIPATH = DATAPATH + 'UNIVERSE/'
    EQPATH = DATAPATH + 'EQUIPMENT/'
    MARKET_PATH = EQPATH + 'market_commodities.ini' # paths to the data we need
    DISTANCE_PATH = FILEPATH + 'dump.csv'

    bases = [] # or load from template

    def __str__(self):
        num_bases = len(self.bases)
        num_commodites = sum([len(comm) for comm in self.bases]) #counts the number of objects inside the bases
        return "this config has {} bases with {} commodies filled".format(num_bases, num_commodites)