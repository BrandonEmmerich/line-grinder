import requests
import pandas as pd

from sportsbooks import utils

HEADERS_PINNY = headers = {
    'authority': 'guest.api.arcadia.pinnacle.com',
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'if-modified-since': 'Wed, 01 Mar 2023 21:06:34 GMT',
    'origin': 'https://www.pinnacle.com',
    'referer': 'https://www.pinnacle.com/',
    'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'x-api-key': 'CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R',
}

URL_PINNY = 'https://guest.api.arcadia.pinnacle.com/0.1/'

class Pinnacle:
    '''
    Scrape for Pinnacle.
    '''
    def __init__(self, league):
        self.league = league
        self.league_id = None
        self.matchups = None
        self.prices = None
        self.df = None

    def get_data(self):
        """
        Get lines data from Pinnacle and wrangle to proper data model.
        """
        self._league_logic()

        if not self.league_id:
            print(f"We don't currently support {self.league}.")
            self.df = utils.empty_dataframe()

        else:
            self._get_matchups()
            self._get_prices()

            self.df = (
                pd.DataFrame(self.matchups)
                .merge(
                    pd.DataFrame(self.prices),
                    on=['matchup_id', 'designation'],
                    how='inner'
                )
            )

    def _get_matchups(self):

        matchups = []

        response = requests.get(
            url=f"{URL_PINNY}leagues/{self.league_id}/matchups?brandId=0",
            headers=HEADERS_PINNY,
        )

        for item in response.json():
            if item['type'] == "matchup":

                row = {
                    'matchup_id': item['id'],
                    'start_time': item['startTime'],
                    'is_live': item['isLive'],
                }

                for participant in item['participants']:
                    details = {
                        'participant_name': participant['name'],
                        'designation': participant['alignment']
                    }

                    matchups.append(dict(row, **details))

        self.matchups = matchups

    def _get_prices(self):
        prices = []

        matchup_ids = {
            x['matchup_id'] for x in self.matchups
        } ## Every matchup_id has two rows, one for each participant.

        for matchup_id in matchup_ids:
            response = requests.get(
                url=f"{URL_PINNY}matchups/{matchup_id}/markets/related/straight",
                headers=HEADERS_PINNY,
            )

            [prices.append(market) for market in self._parse_spread(response)]

        self.prices = prices

    def _parse_spread(self, response):
        markets = []

        for item in response.json():
            if (
                ## Includes only handicap style markets
                item['type'] == 'spread' and
                ## Includes only full-game handicaps
                item['key'].split(';')[1] == '0'
            ):
                row = {
                    'is_alternate': item['isAlternate'],
                    'key': item['key'],
                    'matchup_id': item['matchupId'],
                    'market_type': item['type'],
                }

                for limit in item['limits']:
                    ## Get betting limits for the market: this is the number of dollars you can place on a bet, it changes with time.
                    if limit['type'] == 'maxRiskStake':
                        row.update({'max_risk_stake': limit['amount']})


                for price in item['prices']:
                    markets.append(dict(row, **price))

        return markets

    def _league_logic(self):
        '''
        Translate league name into API league_id
        '''
        if self.league == 'NBA':
            self.league_id = 487
        elif self.league == 'NCAA':
            self.league_id = 493
        else:
            self.league_id = None
