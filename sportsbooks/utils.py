import os
import pandas as pd

def get_mapping(league):
    '''
    Get the mapping dataframe that connects team names between the sports books.
    '''
    if 'analysis' in os.getcwd():
        mapping_path = f"../data/mapping__{league}.csv"

    else:
        mapping_path = f"data/mapping__{league}.csv"

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

def empty_dataframe():
    '''
    Return an empty data frame to use as a placeholder when the markets are empty.
    '''
    empty = pd.DataFrame({
            'participant_name': [],
            'points': [],
            'price': []
            }
        )
    
    return empty