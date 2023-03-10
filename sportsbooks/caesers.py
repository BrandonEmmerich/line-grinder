import numpy as np
import pandas as pd
import requests

from sportsbooks import utils

HEADERS_CAESERS = {
    'authority': 'www.williamhill.com',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'referer': 'https://www.williamhill.com/us/ny/bet/basketball/events/all?id=5806c896-4eec-4de1-874f-afed93114b8c',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'x-app-version': '3.26.0',
    'x-platform': 'cordova-desktop',
    'x-unique-device-id': '63ba23d3-a24d-4ccd-9019-6ce94c3a496a',
}

class Caesers:
    '''
    Caesers
    '''
    def __init__(self, league):
        self.league = league
        self.prices= None
        self.competition_id = None
        self.response = None
        self.df = None

    def get_data(self):
        """
        Get lines data from Caesers and wrangle to proper data model.
        """
        self._league_logic()

        if not self.competition_id:
            print(f"We don't currently support {self.league}.")
            self.df = utils.empty_dataframe()

        else:
            self._get_response()
            self._get_prices()

            if len(self.prices) == 0:
                print('No alternate lines for Caesers yet.')
                self.df = utils.empty_dataframe()

            else:
                self.df = (
                    pd.DataFrame(self.prices)
                    .assign(
                        home_team = lambda x: x['event_name'].transform(lambda s: s.split('| |at| |')[1].replace('|', '')),
                        away_team = lambda x: x['event_name'].transform(lambda s: s.split('| |at| |')[0].replace('|', '')),

                        label_caesers = lambda x: np.where(x['designation'] == 'home', x['home_team'], x['away_team']),
                        price = lambda x: x['decimalOdds'],

                        ## Caesers quotes lines old-school, points is quoting the home team.
                        points = lambda x: np.where(
                            x['designation'] == 'home',
                            x['points'],
                            x['points'] * -1
                            )
                    )
                    .merge(
                        utils.get_mapping(league=self.league),
                        on='label_caesers',
                        how='left'
                    )
                    [['participant_name', 'points', 'price']]
                )

    def _get_response(self):
        url = f'https://www.williamhill.com/us/ny/bet/api/v3/sports/basketball/events/schedule/?competitionIds={self.competition_id}'
        self.response = requests.get(url)

    def _get_prices(self):
        prices = []

        events = [
            x for x in self.response.json()['competitions'][0]['events']
            if not x['started'] # Exclude in-game betting
        ]

        for event in events:
            alternate_spreads = event['markets'][0].get('movingLines')

            if alternate_spreads:
                for price in alternate_spreads['linePrices']:
                    row = {
                        'event_name': event['name'],
                        'start_time': event['startTime'],
                        'points': price['line'],
                    }

                    for selection in price['selections']:
                        details = {
                            'designation': selection['selectionType'],
                            'decimalOdds': selection['price'].get('d'),
                            'americanOdds': selection['price'].get('a')
                        }

                        prices.append(dict(row, **details))

        self.prices = prices

    def _league_logic(self):
        '''
        Translate league name into API league_id
        '''
        if self.league == 'NBA':
            self.competition_id = '5806c896-4eec-4de1-874f-afed93114b8c'
        elif self.league == 'NCAA':
            self.competition_id = 'd246a1dd-72bf-45d1-bc86-efc519fa8e90'
        else:
            self.competition_id = None
