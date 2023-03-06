import numpy as np
import pandas as pd
import requests

from sportsbooks import utils

HEADERS_BETMGM = {
    'authority': 'sports.ny.betmgm.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'referer': 'https://sports.ny.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sports-api-version': 'SportsAPIv1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'x-app-context': 'default',
    'x-bwin-browser-url': 'https://sports.ny.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004',
    'x-from-product': 'sports',
}

URL_BETMGM = 'https://sports.ny.betmgm.com/en/sports/api/widget?layoutSize=Small&page=CompetitionLobby&sportId=7&regionId=9&competitionId=6004&compoundCompetitionId=1:6004&forceFresh=1'

class BetMGM:
    '''
    BetMGM
    '''
    def __init(self):
        self.response = None
        self.lines = None
        self.df = None
        
    def _get_response(self):
        self.response = requests.get(
            url=URL_BETMGM,
            headers=HEADERS_BETMGM,
        )
        
    def _get_lines(self):
        '''
        Get the alternate spread lines from the response JSON.
        '''
        lines = []
        
        # This is where the game information are stored
        fixtures = self.response.json()['widgets'][3]['payload']['items'][0]['activeChildren'][0]['payload']['fixtures']

        for fixture in fixtures:
            row = {
                'fixture_id': fixture['id'],
                'fixture_name': fixture['name']['value'],
            }

            spreads = [
                game for game in fixture['games'] 
                if game['name']['value'] == 'Spread'
            ]

            for spread in spreads:
                results = spread['results']

                for result in results:
                    details = {
                        'result_name': result['name']['value'],
                        'points': result['attr'],
                        'american_odds': result['americanOdds'],
                        'decimal_odds': result['odds']
                    }

                    lines.append(dict(row, **details))
                    
        self.lines = lines

    
    def get_data(self):
        '''
        Get Alt lines data from BetMGM.
        '''
        self._get_response()
        self._get_lines()
        
        self.df = (
            pd.DataFrame(self.lines)
            .assign(
                label_betmgm = lambda x: x['result_name'].apply(utils.clean_name),
                price = lambda x: x['decimal_odds'],
                points = lambda x: x['points'].apply(utils.clean_points),
             )
            .merge(
                utils.get_mapping(),
                on='label_betmgm',
                how='left'
            )
            [['participant_name', 'points', 'price']]
        )
        