import numpy as np
import pandas as pd
import requests

from sportsbooks import utils

HEADERS_WYNN = {
    'authority': 'ny.wynnbet.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'app-name': 'WYNN_NY',
    'client-type': 'DESKTOPWEB',
    'referer': 'https://ny.wynnbet.com/competition/116',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
}

class Wynn:
    '''
    Wynn
    '''
    def __init(self):
        self.lines = []
        self.matches = None
        self.df = None
        
    def _get_matches(self):
        '''
        Get list of NBA matches with odds.
        '''
        params = {
            'filterId': '53',
        }

        response = requests.get(
            'https://ny.wynnbet.com/api/sportsbook/tournaments/v3/116',
            params=params,
            headers=HEADERS_WYNN,
        )
        
        self.matches = [
            {'match_id': x['id'],'matchup_name': x['name']} for x in 
            response.json()['data'][0]['events']
        ]
        
        
    @staticmethod
    def _parse_spreads(self, response):
        
        
        spreads = [
            x for x in response.json()['data']['marketCards'] 
            if x['name'] == 'Spread'
        ]
        
        for market in spreads[0]['markets']:
            row = {
                'points': market['handicapValue']
            }

            outcomes = market['outcomes']
            
            for outcome in outcomes:
                details = {
                    'label_wynn': outcome['name'],
                    'decimalOdds': outcome['prices'][0]['decimal'],
                    'side': outcome['side'],
                }

                self.lines.append(
                    dict(row, **details)
                )
                
    def _get_lines(self):
        self.lines = []
        
        for match in self.matches:
            params = {
                'pageTemplateId': '370',
            }

            response = requests.get(
                f'https://ny.wynnbet.com/api/events/{match["match_id"]}/detail-markets',
                params=params,
                headers=HEADERS_WYNN,
            )
            
            self._parse_spreads(self, response=response)
            
    def get_data(self):
        self._get_matches()
        self._get_lines()
        
        self.df = (
            pd.DataFrame(self.lines)
            .assign(
                price = lambda x: x['decimalOdds'],
             )
            .merge(
                utils.get_mapping(),
                on='label_wynn',
                how='left'
            )
            .assign(
                points = lambda x: np.where(
                    x['side'] == 'Home',
                    x['points'],
                    x['points'] * -1
                )
            )
            [['participant_name', 'points', 'price']]
        )


        

        