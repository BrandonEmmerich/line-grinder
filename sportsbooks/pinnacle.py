import requests
import pandas as pd

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

URL_PINNY = 'https://guest.api.arcadia.pinnacle.com/0.1/leagues/'

class Pinnacle:
    '''
    Scrape for Pinnacle.
    '''
    def __init__(self, league):
        self.league = league
        self.response__matchups = None
        self.df__matchups = None
        self.df__straight = None
        self.df = None
        
    @staticmethod
    def _get(url):
        return requests.get(
            url,
            headers=HEADERS_PINNY
        )
    
    def _get_matchups(self):
        url = URL_PINNY + f'{self.league}/matchups?brandId=0'
        
        matchups = []
        
        response = self._get(url)

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

        self.df__matchups = pd.DataFrame(matchups)
        
     
    def _parse_spread(self, response):
        markets = []
        
        ##TODO: Switch logic for other market types

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
                    if limit['type'] == 'maxRiskStake':
                        row.update({'max_risk_stake': limit['amount']})


                for price in item['prices']:
                    markets.append(dict(row, **price))

        return markets
    
    def _get_spreads(self):
        straight = []
        
        matchup_ids = self.df__matchups.matchup_id.unique().tolist()
        
        for matchup_id in matchup_ids:
            url = f'https://guest.api.arcadia.pinnacle.com/0.1/matchups/{matchup_id}/markets/related/straight'
            response = self._get(url)
            [
                straight.append(market) for market
                in self._parse_spread(response)
            ]
            
        self.df__straight = pd.DataFrame(straight)
        
    def get_data(self):
        self._get_matchups()
        self._get_spreads()
        
        self.df = (
            self.df__matchups
            .merge(
                self.df__straight,
                on=['matchup_id', 'designation'],
                how='outer'
            )
        )
    