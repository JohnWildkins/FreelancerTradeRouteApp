import numpy as np
import pandas as pd
from collections import defaultdict
from config import Config
import re
import time


#Core Functions

def throw_ini_error(err_type):
    print(err_type)

def read_ini(ini_path, v_name='nickname', filter_str=None):
    with open(ini_path, 'r') as ini:
        ini_lines = list(filter(None, [ln.strip() for ln in re.split(r'^(\[[A-Za-z]*\])', ini.read(), flags=re.M)]))
        ds = next(i for i, string in enumerate(ini_lines) if '[' in string)
        i_comments = ini_lines[:ds]
        i_keys = ini_lines[ds::2]
        i_values = ini_lines[ds+1::2]
        ini_dict = dict()

        for i in range(len(i_keys)):
            if filter_str and filter_str.lower() not in i_keys[i].lower():
                continue

            value_name = i_keys[i]
            i_tuples = list()

            try:
                i_props = list(filter(None, [ip for ip in i_values[i].split('\n') if ';' not in ip]))
            except IndexError:
                throw_ini_error(IndexError)
                continue

            if not i_props:
                continue

            for ip in i_props:
                i_tuples.append(tuple([i_tup.strip() for i_tup in ip.split('=')]))

            if not i_tuples:
                continue

            partial_dict = defaultdict(list)
            try:
                for k, v in i_tuples:
                    if v_name in k:
                        value_name = v
                    partial_dict[k].append(v)
            except ValueError:
                print('ERR: Invalid INI entry in file {0}'.format(ini_path))

            ini_dict[value_name] = partial_dict

    return ini_dict

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


    #distances = pd.read_csv(distances_path, names = ['start', 'end', 'time'])
    #distances = distances[distances['start']!=distances['end']]
    #distances = distances[distances['time']!=-1]

    distances = pd.read_csv(distances_path, names = ['start', 'end', 'time'])
    distances = distances.set_index(['start', 'end'])
    distances['time'] = distances['time'].apply(lambda x: x + 20000) # adding dock time because that's not exported for some reason

    commodities = dict()
    bases = dict()
    infocards = dict()
    sys_ids = dict()
    system_files = dict()
    systems = dict()

    # TODO: Separate out into helper functions; make a specialized class for this and generalize config parsing

    with open(Config.FILEPATH + 'SERVICE/infocards.txt', 'r', encoding='utf8') as i:
        for line in i:
            if line.strip().isdigit():
                next(i, None)
                infocards[line.strip()] = next(i, None)

    select_equip = read_ini(Config.FILEPATH + 'DATA/EQUIPMENT/select_equip.ini', filter_str="commodity")
    goods = read_ini(Config.FILEPATH + 'DATA/EQUIPMENT/goods.ini')
    market_commodities = read_ini(comm_markets_path, 'base')
    u_systems = read_ini(Config.FILEPATH + 'DATA/UNIVERSE/universe.ini', filter_str="system")
    u_bases = read_ini(Config.FILEPATH + 'DATA/UNIVERSE/universe.ini', filter_str="base")

    for k, v in select_equip.items():
        commodities[k.lower()] = {
            "nickname": k.lower(),
            "ids_name": v['ids_name'],
            "display_name": "",
            "base_price": 0.0,
            "consumed_by": [],
            "produced_by": []
            }

    for k, v in goods.items():
        if k.lower() not in commodities.keys():
            continue
        commodities[k.lower()]["base_price"] = float(v['price'][0])

    for k, v in market_commodities.items():
        bases[k.lower()] = {
            "nickname": k.lower(),
            "ids_name": "",
            "display_name": "",
            "archetype": "",
            "system": "",
            "commodities": {}
        }

        for mgs in v['MarketGood']:
            mg = mgs.split(', ')
            raw_data = [m for m in mg]
            commo = mg.pop(0).lower()
            base = bases[k.lower()]['commodities']
            base[commo] = {
                'raw_data': raw_data,
                'price_mult': float(mg.pop()),
                'consumer': int(mg.pop()),
                'max': int(mg.pop()),
                'min': int(mg.pop()),
                'rep': float(mg.pop()),
                'rank': int(mg.pop()),
                'display_name': infocards[commodities[commo]["ids_name"][0]].strip()
            }

            base[commo]['actual_price'] = base[commo]['price_mult'] * commodities[commo]['base_price']

            if base[commo]['price_mult'] > 1.0 or base[commo]['consumer']:
                commodities[commo]['consumed_by'].append(bases[k.lower()])
            if not base[commo]['consumer']:
                commodities[commo]['produced_by'].append(bases[k.lower()])

    for k, v in u_systems.items():
        sys_ids[k.lower()] = v['strid_name'][0]
        if 'file' in v.keys(): # thanks multiuniverse plugin, very cool
            system_files[k.lower()] = v['file'][0]

    for k, v in u_bases.items():
        try:
            bases[k.lower()]["ids_name"] = v['strid_name'][0].lower()
            bases[k.lower()]["system"] = v['system'][0].lower()
        except KeyError:
            pass

    for b_name, b_dict in bases.items():
        strid_name = b_dict['ids_name']
        system = b_dict['system']
        try:
            sys_strid_name = sys_ids[system]
        except KeyError:
            print(b_dict)
        system_path = ""

        try:
            system_path = system_files[system]
        except KeyError:
            print("WARN: Path not found for system '{0}'.".format(system))
        if system not in systems.keys():
            systems[system] = read_ini(Config.UNIPATH + system_path)

        if strid_name == "0":
            b_dict["display_name"] = strid_name
            continue
        try:
            b_dict["display_name"] = infocards[strid_name].strip()
        except KeyError:
            b_dict["display_name"] = strid_name
            print("ERR: No IDS {0} found in infocards.txt for {1}!".format(strid_name, b_name))

        try:
            b_dict["system_dis"] = infocards[sys_strid_name].strip()
        except KeyError:
            b_dict["system_dis"] = sys_strid_name
            print("ERR: No IDS {0} found in infocards.txt for {1}!".format(sys_strid_name, system))

    for c_name, c_dict in commodities.items():
        strid_name = c_dict["ids_name"][0]
        try:
            c_dict["display_name"] = infocards[strid_name].strip()
        except KeyError:
            c_dict["display_name"] = c_name
            print("ERR: No IDS {0} found in infocards.txt for {1}".format(strid_name, c_name))

    with open('help.txt', 'w') as w:
        w.write(str(commodities['commodity_credit1']['produced_by']))

    return distances, bases, commodities

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
