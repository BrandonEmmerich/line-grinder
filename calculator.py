class Calculator:

    @staticmethod
    def convert_american_to_decimal(american_odds):

        if abs(american_odds) < 100:
            raise ValueError('American Odds must be quoted like -110, +120')

        if american_odds > 0:
            return (american_odds / 100) + 1

        else:
            return (-100 / american_odds ) + 1
        
    @staticmethod
    def convert_decimal_to_american(decimal):
        
        if abs(decimal) >= 100:
            raise ValueError('You might have gotten some American odds, check again')
            
        if decimal >= 2:
            return (decimal -1) * 100
        
        else:
            return -100/(decimal -1)
        
    @staticmethod    
    def get_implied_probability(line):
        '''
        Assuming American Odds
        '''
        if line >= 100:
            return 100 / (100 + line)
        else:
            return line / (-100 + line)

