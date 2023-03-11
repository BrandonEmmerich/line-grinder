import pandas as pd
import requests

from sportsbooks import utils

HEADERS_DRAFTKINGS = {
    'authority': 'sportsbook-us-ny.draftkings.com',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'origin': 'https://sportsbook.draftkings.com',
    'referer': 'https://sportsbook.draftkings.com/',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
}

PARAMS = {'format': 'json'}

class DraftKings:
    '''
    DraftKings
    '''
    def __init__(self, league):
        self.league = league
        self.sub_category = None
        self.event_group = None
        self.response = None
        self.prices = None
        self.df = None

    def get_data(self):
        """
        Get lines data from DraftKings and wrangle to proper data model.
        """
        self._league_logic()

        if not self.sub_category:
            print(f"We don't currently support {self.league}.")
            self.df = utils.empty_dataframe()

        else:
            self._get_response()
            self._get_prices()

            self.df = (
                pd.DataFrame(self.prices)
                .merge(
                    utils.get_mapping(self.league),
                    left_on='label',
                    right_on='label_draftkings'
                )
                .assign(
                    price = lambda x: x['oddsDecimal'],
                    points = lambda x: x['line']
                )
                [['participant_name', 'points', 'price']]
            )

    def _get_response(self):
        url = f"""https://sportsbook-us-ny.draftkings.com//sites/US-NY-SB/api/v5/eventgroups/{self.event_group}/categories/487/subcategories/{self.sub_category}"""

        self.response = requests.get(
            url=url,
            headers=HEADERS_DRAFTKINGS,
            params=PARAMS
        )

    def _get_prices(self):
        if not self.response.json().get('eventGroup'):
            print('No alt lines for DraftKings.')
            self.df = utils.empty_dataframe()

        else:
            games = [
                x for x in self.response.json()['eventGroup']['offerCategories'][0]['offerSubcategoryDescriptors']
                if x['name'] == 'Alternate Spread' ## Only get Alternate Spreads, Ignore Alternate Totals, and Halftime/Fulltime splits.
            ][0]['offerSubcategory']['offers']

            prices = []

            for game in games:
                outcomes = game[0]['outcomes']
                for outcome in outcomes:
                    prices.append(outcome)

            self.prices = prices

    def _league_logic(self):
        '''
        Translate league name into API league_id
        '''
        if self.league == 'NBA':
            self.sub_category = 4606
            self.event_group = 42648
        elif self.league == 'NCAA':
            self.sub_category = 10317
            self.event_group = 92483
        else:
            self.sub_category = None
            self.event_group = None
