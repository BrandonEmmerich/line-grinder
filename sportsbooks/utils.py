import os
import pandas as pd

def get_mapping():
    '''
    Get the mapping dataframe that connects team names between the sports books.
    '''
    if 'analysis' in os.getcwd():
        mapping_path = '../data/mapping.csv'

    else:
        mapping_path = 'data/mapping.csv'

    return pd.read_csv(mapping_path)

def clean_name(name):
    '''
    The sportsbook returns names that look like this: Dallas Mavericks -9.5
    We want names that look like this: Dallas Mavericks
    '''
    name = name.split(' -')[0]
    name = name.split(' +')[0]

    return name

def clean_points(points):
    return float(points.replace('+', ''))