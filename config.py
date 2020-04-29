import os


class Base(object):
     commod_list = [] #to be iteratively filled with all the commodities the base handles

class Config(object):
    bases = [] # or load from template

    def __str__(self):
        num_bases = len(self.bases)
        num_commodites = sum([len(comm) for comm in self.bases]) #counts the number of objects inside the bases
        return "this config has {} bases with {} commodies filled".format(num_bases, num_commodites)