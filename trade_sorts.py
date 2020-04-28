import numpy as np 
import pandas as pd




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
    bases(list of dictonaries): list containing all of the base entries in market_commodities.ini in dictonary 
    form. Dictonaies hold base_code, base_name, and list of commodities traded. 
    comm_set (set): set of all commodities bought or sold on all bases
    base_names (list): all base names
    '''


    distances = pd.read_csv(distances_path, names = ['start', 'end', 'time'])
    distances = distances[distances['start']!=distances['end']]
    distances = distances[distances['time']!=-1]

    with open(comm_markets_path, 'r') as file:
        lines = file.readlines() 
    
    comment_count = 0
    bases = []
    commodities =[]
    for i in lines[2:]:
        if i.lower() == '[basegood]\n' or i == ';EVERYTHING BELOW THIS LINE IS DATABASE.':
            if comment =='':
                comment = base_code
            bases.append({'base_code':base_code, 'Name':comment, 'commodities':commodities})
            commodities=[]
            comment = ''
            comment_count = 0
        if i[:4].lower() == "base":
            base_code = i[7:]
        if i[:1] == ';' and comment_count == 0:
            comment = i
            comment_count+=1
        elif i[:1]==';':
            print(i)
            comment +'\n'+ i
        if i[:10].lower() == 'marketgood':
            t =i[13:].split()
            l = [float(j.strip(',')) for j in t[1:6]]
            l.append(float(t.pop()))
            l.append(t[0])
            commodities.append(l)
    
    comm_set = set([])
    for i in bases: #this loop in loop adds all the commodities to a set so we know how many commodities to display in our applet
        j = i['commodities']
        for k in j:
            comm_set.add(k[6])
    base_names=[(base['Name'],base['base_code']) for base in bases]
    
    return distances, bases, comm_set, base_names


def which_sell(commodity_list):
    '''
    A helperfunction that digs through bases and finds which ones sell any of a given list of commodities
    
    Paramaters
    commodity_list(list): a list of the commodity codes (strings) you want to find where they're sold
    
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