import numpy as np
import pandas as pd
from collections import defaultdict
from config import Config
import re


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

    commodities = dict()
    bases = dict()
    infocards = dict()
    sys_ids = dict()
    system_files = dict()

    # TODO: Separate out into helper functions; make a specialized class for this and generalize config parsing

    with open(Config.FILEPATH + 'SERVICE/infocards.txt', 'r', encoding='utf8') as i:
        for line in i:
            if line.strip().isdigit():
                next(i, None)
                infocards[line.strip()] = next(i, None)

    with open(Config.FILEPATH + 'DATA/EQUIPMENT/select_equip.ini', 'r') as e:
        for line in e:
            if "=" in line:
                e_type, e_data = (e.strip().lower() for e in line.split('=', maxsplit=1))
                if "nickname" in e_type and "commodity" in e_data:
                    commodities[e_data] = {
                        "strid_name": "",
                        "display_name": "",
                        "base_price": 0.0,
                        "consumed_by": [],
                        "produced_by": []
                    }
                    commodities[e_data]["strid_name"] = next(e).split('=', maxsplit=1)[1].strip().lower()

    with open(Config.FILEPATH + 'DATA/EQUIPMENT/goods.ini', 'r') as g:
        current_commod = ""
        for line in g:
            if "=" in line:
                g_type, g_data = (g.strip().lower() for g in line.split('=', maxsplit=1))
                if "nickname" in g_type:
                    current_commod = g_data
                if g_type == "price" and current_commod in commodities:
                    commodities[current_commod]["base_price"] = float(g_data)

    with open(comm_markets_path, 'r') as f:
        base = ""
        for line in f:
            if "=" in line:
                i_type, i_data = (i.strip().lower() for i in line.split('=', maxsplit=1))
                if "base" in i_type:
                    bases[i_data] = {
                        "strid_name": "",
                        "display_name": "",
                        "archetype": "",
                        "system": "",
                        "commodities": {}
                    }
                    base = i_data
                elif "marketgood" in i_type:
                    i_data = i_data.split(",")
                    i_commod = i_data.pop(0)
                    bases[base]["commodities"][i_commod] = {
                        'raw_data': [float(i) for i in i_data],
                        'price_mult': float(i_data.pop()),
                        'consumer': int(i_data.pop()), # this isn't actually a flag for buying / selling, but we can use it as one since it's ignored
                        'max': int(i_data.pop()),
                        'min': int(i_data.pop()),
                        'rep': float(i_data.pop()),
                        'rank': int(i_data.pop()),
                        'display_name': infocards[commodities[i_commod]["strid_name"]].strip()
                        }
                    bases[base]["commodities"][i_commod]['actual_price'] = bases[base]["commodities"][i_commod]['price_mult'] * commodities[i_commod]['base_price']
                    if bases[base]["commodities"][i_commod]['consumer'] or bases[base]["commodities"][i_commod]['price_mult'] > 1.0:
                        commodities[i_commod]['consumed_by'].append(bases[base])
                    if not bases[base]["commodities"][i_commod]['consumer']:
                        commodities[i_commod]['produced_by'].append(bases[base])

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
                        sys_ids[u_data] = ""
                        sys = u_data
                    else:
                        base = u_data
                elif "strid_name" in u_type:
                    if system:
                        sys_ids[sys] = u_data
                    else:
                        try:
                            bases[base]["strid_name"] = u_data
                        except:
                            pass
                            # print("WARN: Base {0} found in universe.ini, but not in market_commodities.ini. May be intentional.".format(base))
                elif "system" in u_type:
                    try:
                        bases[base]["system"] = u_data
                        bases[base]["system_dis"] = ""
                    except KeyError:
                        continue
                elif "file" in u_type and system:
                    system_files[sys] = u_data

    systems = dict()

    for b_name, b_dict in bases.items():
        strid_name = b_dict['strid_name']
        system = b_dict['system']
        sys_strid_name = sys_ids[system]
        system_path = ""

        try:
            system_path = system_files[system]
        except KeyError:
            print("WARN: Path not found for system '{0}'.".format(system))
        if system not in systems.keys():
            systems[system] = {}
            with open(Config.UNIPATH + system_path, 'r') as sys:
                sys_lines = list(filter(None, [sn.strip() for sn in re.split(r'^\[([A-Za-z]*)\]', sys.read(), flags=re.M)]))
                sys_keys = [s.lower() for s in sys_lines[::2]]
                sys_values = sys_lines[1::2]
                sys_dict = systems[system]
                for s in range(len(sys_keys)):
                    s_tuples_raw = []
                    try:
                        s_props = [sys for sys in sys_values[s].split('\n') if ';' not in sys]
                    except IndexError:
                        print("ERR: Got IndexError while unpacking values in system {0}.".format(system))
                    for sp in s_props:
                        s_tuples_raw.append(tuple([s_tup.strip().lower() for s_tup in sp.split('=')]))
                    if not s_tuples_raw or len(s_props) < 2:
                        continue
                    if 'nickname' in s_tuples_raw[0][0]:
                        nickname = s_tuples_raw.pop(0)
                        try:
                            sys_dict[nickname[1]] = {s_type: s_data for s_type, s_data in s_tuples_raw}
                        except ValueError:
                            print("ERR: Got ValueError while unpacking sysinfo tuple in system {1}: {0}".format(s_tuples_raw, system))
                    else:
                        try:
                            sys_dict[sys_keys[s]] = {s_type: s_data for s_type, s_data in s_tuples_raw}
                        except ValueError:
                            print(s_props)
                            print("ERR: Got ValueError while unpacking sysinfo tuple in system {1}: {0}".format(s_tuples_raw, system))

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
        strid_name = c_dict["strid_name"]
        try:
            c_dict["display_name"] = infocards[strid_name].strip()
        except KeyError:
            c_dict["display_name"] = c_name
            print("ERR: No IDS {0} found in infocards.txt for {1}".format(strid_name, c_name))

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
