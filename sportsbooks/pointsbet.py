import os
import pandas as pd
import requests

from sportsbooks import utils

HEADERS_POINTSBET = {
    'authority': 'api.ny.pointsbet.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'if-modified-since': 'Sat, 04 Mar 2023 19:06:52 GMT',
    'origin': 'https://ny.pointsbet.com',
    'referer': 'https://ny.pointsbet.com/',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
}

class PointsBet:
    '''
    PointsBet
    '''
    def __init__(self):
        self.events = None
        self.matchups = None
        self.df__raw = None 
        
    @staticmethod
    def _get(url):
        return requests.get(
            url,
            headers=HEADERS_POINTSBET
        )

    def _get_matchups(self):
        url = 'https://api.ny.pointsbet.com/api/v2/competitions/105/events/featured?includeLive=false&page=1'
        response = self._get(url)

        matchups = []

        for item in response.json()['events']:
            if item['isLive'] == False:
                ## Exclude in-game betting for now.
                row = {
                    'competition_key': item['key'],
                    'competition_name': item['name'],
                    'start_time': item['startsAt']
                }
                matchups.append(row)

        self.matchups = matchups
       
        
    def get_data(self):
        
        self._get_matchups()
        self._get_alt_lines()
        
        self.df = (
            self.df__raw
            .assign(
                label_pointsbet = lambda x: x['name'].apply(utils.clean_name)
            )
            .merge(
                utils.get_mapping(),
                on='label_pointsbet',
            )
            .assign(
                odds_decimal = lambda x: x['price'],
            )
            [['participant_name', 'points', 'odds_decimal']]
        )
        
    def _get_alt_lines(self):
        lines = []
        
        for matchup in self.matchups:
            matchup_id = matchup['competition_key']
            url = f'https://api.ny.pointsbet.com/api/mes/v3/events/{matchup_id}'
            response = self._get(url)
            

            for market in response.json()['fixedOddsMarkets']:
                if market['eventName'] == 'Pick Your Own Line':
                    outcomes = market['outcomes']
                    for outcome in outcomes:
                        lines.append(outcome)
                        
        self.df__raw = pd.DataFrame(lines)

