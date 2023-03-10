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

URL_POINTSBET = "https://api.ny.pointsbet.com/api"

class PointsBet:
    '''
    PointsBet
    '''
    def __init__(self, league):
        self.league = league
        self.league_id = None
        self.matchups = None
        self.prices = None
        self.df = None

    def get_data(self):
        """
        Get lines data from PointsBet and wrangle to proper data model.
        """
        self._league_logic()

        if not self.league_id:
            print(f"We don't currently support {self.league}.")
            self.df = utils.empty_dataframe()

        else:
            self._get_matchups()
            self._get_prices()

            if len(self.prices) == 0:
                ## Sometimes there are no alternate lines
                print('No alternate lines for PointsBet.')
                self.df = utils.empty_dataframe()

            else:

                self.df = (
                    pd.DataFrame(self.prices)
                    .assign(label_pointsbet = lambda x: x['name'].apply(utils.clean_name))
                    .merge(
                        utils.get_mapping(self.league), ## Map PointsBet names to master list.
                        on='label_pointsbet',
                        how='left'
                    )
                    [['participant_name', 'points', 'price']]
                )

    def _league_logic(self):
        '''
        Translate league name into API league_id
        '''
        if self.league == 'NBA':
            self.league_id = 105
        elif self.league == 'NCAA':
            self.league_id = 21
        else:
            self.league_id = None

    def _get_matchups(self):
        """
        Paginate through Pointsbet to get list of all matchups.
        """
        page_number = 1
        matchups = []

        while True:

            response = requests.get(
                url=f"{URL_POINTSBET}/v2/competitions/{self.league_id}/events/featured?includeLive=false&page={page_number}",
                headers=HEADERS_POINTSBET,
            )

            for item in response.json()['events']:
                if not item['isLive']:
                    ## Exclude in-game betting for now.
                    row = {
                        'competition_key': item['key'],
                        'competition_name': item['name'],
                        'start_time': item['startsAt']
                    }
                    matchups.append(row)

            if response.json().get('nextPage'):
                page_number = response.json().get('nextPage')
            else:
                break

        self.matchups = matchups

    def _get_prices(self):
        """
        For each matchup, get the market prices.
        """
        prices = []

        for matchup in self.matchups:
            matchup_id = matchup['competition_key']

            response = requests.get(
                url=f"{URL_POINTSBET}/mes/v3/events/{matchup_id}",
                headers=HEADERS_POINTSBET,
            )

            for market in response.json()['fixedOddsMarkets']:
                if (
                    market['eventName'] == 'Pick Your Own Line'
                ):  ## Get the alternate spreads
                    outcomes = market['outcomes']
                    for outcome in outcomes:
                        prices.append(outcome)

        self.prices = prices
