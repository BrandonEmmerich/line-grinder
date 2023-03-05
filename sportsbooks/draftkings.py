import pandas as pd
import requests

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
    def __init__(self, league, category_id):
        self.league = league
        self.category_id = category_id
        self.response__alt_lines = None
        self.df__raw = None


    def _hit_endpoints(self):
        self.response__alt_lines = requests.get(
            f'https://sportsbook-us-ny.draftkings.com//sites/US-NY-SB/api/v5/eventgroups/42648/categories/{self.league}/subcategories/{self.category_id}',
            headers=HEADERS_DRAFTKINGS,
            params=PARAMS
        )

    def _unpack_json(self):
        games = self.response__alt_lines.json()['eventGroup']['offerCategories'][0]['offerSubcategoryDescriptors'][1]['offerSubcategory']['offers']

        lines = []

        for game in games:
            outcomes = game[0]['outcomes']
            for outcome in outcomes:
                lines.append(outcome)

        self.df__raw = pd.DataFrame(lines)
        
    def _get_alt_lines(self):
        self._hit_endpoints()
        self._unpack_json()
        
    def get_data(self):
        mapping = pd.read_csv('data/mapping.csv')
        
        self._get_alt_lines()
        
        self.df = (
            self.df__raw
            .merge(
                mapping,
                left_on='label',
                right_on='label_draftkings'
            )
            .assign(
                price = lambda x: x['oddsAmerican'].astype(int),
                points = lambda x: x['line']
            )
            [['participant_name', 'points', 'price']]
        )
        
        
        

