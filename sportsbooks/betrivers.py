import pandas as pd
import requests

from sportsbooks import utils

HEADERS_KAMBI = {
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

URL_KAMBI = "https://eu-offering-api.kambicdn.com/offering/v2018"

PARAMS = {
    'lang': 'en_US',
    'market': 'US-NY',
    'client_id': '2',
    'channel_id': '1',
    'includeParticipants': 'true',
}

class BetRivers:
    '''
    BetRivers. Fun fact, it seems like BetRivers and Barstool are all sourcing their lines from a third party source: https://www.kambi.com/
    '''
    def __init__(self, league):
        self.league = league
        self.league_id = None
        self.matchups = None
        self.prices = None
        self.df = None

    def get_data(self):
        """
        Get lines data from BetRivers and wrangle to proper data model.
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
                print('No alternate lines for BetRivers.')
                self.df = utils.empty_dataframe()

            else:

                self.df = (
                    pd.DataFrame(self.prices)
                    .assign(
                        ## Both the spread (line) and the decimal odds (odds) are quoted in units 1000x too big.
                        points = lambda x: x['line'] / 1000,
                        price = lambda x: x['odds'] / 1000
                    )
                    .merge(
                        utils.get_mapping(self.league), ## Map BetRivers names to master list.
                        left_on='englishLabel',
                        right_on='label_kambi',
                        how='left'
                    )
                    [['participant_name', 'points', 'price']]
                )

    def _league_logic(self):
        '''
        Translate league name into API league_id
        '''
        if self.league == 'NBA':
            self.league_id = 'basketball/nba'
        elif self.league == 'NCAA':
            self.league_id = 'basketball/ncaab'
        else:
            self.league_id = None

    def _get_matchups(self):
        """
        Get all event IDs from Kambi API
        """

        url = URL_KAMBI + f"/pivuspa/listView/{self.league_id}/all/all/matches.json?market=US&market=US&includeParticipants=true&useCombined=true&lang=en_US"

        response = requests.get(
            url,
            headers=HEADERS_KAMBI,
            timeout=3
        )

        matchups = [
            event['event']['id'] for event in response.json()['events']
        ]

        self.matchups = matchups

    def _get_prices(self):
        """
        For each matchup, get the market prices.
        """
        prices = []

        for event_id in self.matchups:

            response = requests.get(
                f'https://eu-offering.kambicdn.org/offering/v2018/rsiusny/betoffer/event/{event_id}.json',
                params=PARAMS,
                headers=HEADERS_KAMBI,
                timeout=3
            )

            if response.status_code == 200:

                offers = [
                    offer for offer in response.json()['betOffers']
                    if offer['criterion'].get('label') == "Point Spread"
                ]

                for offer in offers:
                    for outcome in offer['outcomes']:
                        prices.append(outcome)


        self.prices = prices
