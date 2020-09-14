import numpy as np
import pandas as pd
from collections import defaultdict
from config import Config


#Core Functions

def get_data(comm_markets_path, distances_path):
    '''
    A function that pulls in the data from marketcommodities.ini and the flc dump file and scrapes it.
    +++++++++
    Parameters:
    comm_markets_path (str): the path of market_commodities.ini
    distances_path (str): the path of the flc dump file
    +++++++++
    Returns
    distances (Dataframe): pandas dataframe of all the viable distances between bases
    bases(nested dict): dictionary structure keys internal name to a dictionary containing every commodity bought and sold
    comm_set (list): list of all commodities bought or sold on all bases
    base_names (dict): all base names keyed to their internal name
    sys_names (dict): all system names keyed to their internal name
    '''


    distances = pd.read_csv(distances_path, names = ['start', 'end', 'time'])
    distances = distances[distances['start']!=distances['end']]
    distances = distances[distances['time']!=-1]

    bases = {}
    commodities = set([])
    commod_ids = {}
    commod_names = {}
    base_ids = {}
    sys_ids = {}
    base_names = {}
    sys_names = {}
    infocards = {}

    with open(comm_markets_path, 'r') as f:
        base = ""
        for line in f:
            if "=" in line:
                i_type, i_data = (i.strip().lower() for i in line.split('=', maxsplit=1))
                if "base" in i_type:
                    bases[i_data] = {}
                    base = i_data
                elif "marketgood" in i_type:
                    i_data = i_data.split(",")
                    i_commod = i_data.pop(0)
                    commodities.add(i_commod)
                    bases[base][i_commod] = [float(i) for i in i_data]

    commodities = sorted(commodities)

    with open(Config.FILEPATH + 'DATA/UNIVERSE/universe.ini', 'r') as u:
        base = ""
        sys = ""
        system = False
        for line in u:
            if "[system]" in line.lower():
                system = True
            elif "[base]" in line.lower():
                system = False
            if "=" in line:
                u_type, u_data = (u.strip().lower() for u in line.split('=', maxsplit=1))
                if "nickname" in u_type:
                    if system:
                        sys_ids[u_data] = {}
                        sys = u_data
                    else:
                        base_ids[u_data] = {}
                        base = u_data
                elif "strid_name" in u_type:
                    if system: sys_ids[sys][u_type] = u_data
                    else: base_ids[base][u_type] = u_data
                elif "system" in u_type:
                    base_ids[base][u_type] = u_data

    with open(Config.FILEPATH + 'DATA/EQUIPMENT/select_equip.ini', 'r') as e:
        for line in e:
            if "=" in line:
                e_type, e_data = (e.strip().lower() for e in line.split('=', maxsplit=1))
                if "nickname" in e_type and "commodity" in e_data:
                    commod_ids[e_data] = next(e).split('=', maxsplit=1)[1].strip().lower()

    with open(Config.FILEPATH + 'SERVICE/infocards.txt', 'r', encoding='utf8') as i:
        for line in i:
            if line.strip().isdigit():
                next(i, None)
                infocards[line.strip()] = next(i, None)

        for b_name, b_dict in base_ids.items():
            strid_name = b_dict['strid_name']
            if strid_name == "0":
                base_names[b_name] = b_name
                continue
            try:
                base_names[b_name] = infocards[strid_name].strip()
            except KeyError:
                base_names[b_name] = b_name
                print("ERR: No IDS {0} found in infocards.txt for {1}!".format(strid_name, b_name))

        for commod in commodities:
            strid_name = commod_ids[commod]
            try:
                commod_names[commod] = infocards[strid_name].strip()
            except KeyError:
                commod_names[commod] = commod
                print("ERR: No IDS {0} found in infocards.txt for {1}".format(strid_name, commod))


    return distances, bases, commodities, base_names, sys_names, commod_names


def which_sell(bases, commodity_list):
    '''
    A helperfunction that digs through bases and finds which ones sell any of a given list of commodities
    
    Paramaters
    commodity_list(list): a list of the commodity codes (strings) you want to find where they're sold
    bases (list of dictonaries): a raw read of the marketcommodities.ini as a dictonary
    Returns
    list of bases (list): list of base codes that sell any of the given commodities
    '''
    sells_set = set([])
    for i in bases:
        for k in i['commodities']:
            if k[-1] in commodity_list and k[-3]== 0:
                sells_set.add(i['base_code'])
    l = list(sells_set)
    return [i.strip('\n') for i in l]

def lookup(bases):
    '''
    A helperfunction to produce a pair of dictonaries that associate base codes to base names and back again. 
    +++++++++
    Parameters
    bases (list of dictonaries): a raw read of the marketcommodities.ini as a dictonary

    +++++++++
    Returns
    two dictonaries for fast lookup of name/code relationship. 
    base_code_lookup (dict): keys as names, codes as values
    base_name_lookup (dict): keys as codes, names as values
    '''
    keys = [base['Name'].strip('\n') for base in bases]
    values = [base['base_code'].strip('\n').lower() for base in bases]
    base_code_lookup = {keys[i]: values[i] for i in range(len(keys))} 
    base_name_lookup = {values[i]:keys[i] for i in range(len(keys))}
    return base_code_lookup, base_name_lookup

def commodities_from_config(config):
    '''
    takes the config (whatever that turns out to be like, right now its a list of lists) and spits out all of the commodites used
    '''
    
    comm_set = set()
    for locations in config:
        comm_set.update(locations[1])
        comm_set.update(locations[2])
        comm_set.update(locations[3])
    return comm_set    

def sort_by_closest_base(list_of_bases, distances):
    '''
    a function that takes the distances dataframe and any list of bases and sorts all the other bases out into the lists of bases closest to those bases in the list of bases. 
    Its got a lot of fuckery, and maybe can be given aother pass for better algorithmic complexity. I'm so sorry. 
    
    Parameters 
    list_of_bases (list): a list of string base codes
    distances (DataFrame): the base to base travel times from flcomp formatted as a DataFrame by get_data()
    
    Returns:
    sorted_l (list of lists) list of list of bases, sorted in the same shape as the list of bases fed in, 
    with each list containing those bases that are closest to the base listed at the same index in list_of_bases
    '''
    k = [distances[distances['start'] == i] for i in list_of_bases] # makes a list of dataframes of routes starting from the bases in question
    k = [i[~i['end'].isin(list_of_bases)].reset_index() for i in k] # gets rid of routes between bases in the  list
    
    df = pd.DataFrame()
    for idx, i in enumerate(list_of_bases): #peices the list k back together into a larger thing
        df[i]=k[idx]['time']
    df['base'] = k[0]['end']
    df = df.set_index('base')

    sorted_bases = df.idxmin(axis=1)
    sorted_bases = sorted_bases.reset_index()
    sorted_l =[]

    for i in list_of_bases:
        sorted_l.append(sorted_bases[sorted_bases[0]==i]['base'].to_list())

    return sorted_l

def gen_market_from_config(config, distances):
    '''
    function that reads the config file(currently a list of lists) and turns that into a dictonary much closer to the marketgoods ini for the backwards-parser to turn into a text file. 
 
    Parameters
    ++++++++
    config (list of lists): bases that buy and sell each commodity, formatted into a list containing [base name, commodity base produces, comody base resells, comodity base consumes]
    distances(df): dataframe of all base to base travel times
    ++++++++
    Returns
    market_goods(defaultdict(list)):
    '''
    
    comms = commodities_from_config(config)
    
    
    #loop that rolls through the config file and sorts out the bases that consume and produce each thing. 
    market = []
    for commodity in comms:
        bases_that_consume = []
        bases_that_produce = []
            
        for base in config:
            if commodity in base[1]:
                bases_that_produce.append(base[0])
            if commodity in base[3]:
                bases_that_consume.append(base[0])
        
        market.append({'commodity': commodity, 'produces':bases_that_produce,'consumes':bases_that_consume})
    
    
    #loop that takes the market produced above and turns it into a dictonary of bases, commodities, buy-sells, and travel ties. 
    market_goods = defaultdict(list)
    for commodity in market:
    #print(market_goods)
        specific_distances = distances[distances['start'].isin(commodity['produces'])]
        
   
        for location in commodity['produces']:
            market_goods[location].append((commodity['commodity'], 'sells', 1 )) #sets distance for sellers to 1 for purposes of multiplying price by 1. 
        
        sorts = sort_by_closest_base(commodity['produces'], specific_distances)
        #print(sorts)
        consumer = commodity['consumes']
        
        filter_sorts = [[base for base in group if base[1] in consumer] for group in sorts] #nasty comprehension in a comprehension filters out all the bases that are not set as consumers of the commodity
        
        for group in filter_sorts:
            for location in group:
                market_goods[location[1]].append((commodity['commodity'], 'buy', location[0]))
                
                
    return market_goods

def find_nearest_x(base_code, num, distances):
    '''
    given the list of distances, finds the nearest num bases to base given
    ++++++++++
    Parameters:
    base_code (str): base you want to find closest guys to
    num (int): number of bases to return
    distances(dataframe): pandas DF of all base to base travel times. 
    ++++++++++
    Returns:
    output (lst): list of bases that are n closest to base given
    '''
    output = distances[distances['start'] == base_code].sort_values('time', axis = 0).head(num)['end'].to_list()
    return output

def write_ini(file_path, market, config, base_name_lookup):
    '''
    function that takes the market dictonary and formats it for freelancer, and saves it as a text file
    ++++++++++
    Parameters
    file_path (str): name and path of file
    market (defaultdict(list)): per base formatting of all commodities
    config: file that configures the pricing
    base_name_lookup (dict): looks up names from base codes
    ++++++++++
    Returns:
    none, 
    writes a file
    '''
    lines = []
    for item in market.keys():

        lines.append('[BaseGood]')
        lines.append('base = '+ item)
        lines.append(';'+base_name_lookup[item])

        for commodity in market[item]:
            if commodity[1] == 'sells':
                function_tag = '1'
            else:
                function_tag = '0'
            price_mult = str(commodity[2]) # For a working version, this needs to reference something in config to set prices
            mgood =['Marketgood =',commodity[0],'0, -1, 0, 0,', function_tag, str(commodity[2])]
            lines.append(' '.join(mgood))

    with open(file_path, 'w') as f:
        for line in lines:
            f.write(line+'\n')
