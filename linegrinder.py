import matplotlib.pyplot as plt
import pandas as pd
import pendulum
import sys
sys.path.append('..')

from sportsbooks import (
    pinnacle,
    draftkings,
    pointsbet,
    caesers,
    betmgm
)

from calculator import Calculator

def right_now():
    return str(pendulum.now()).split('.')[0].replace('T', ' ')

def main():

    league=487
    pinny = pinnacle.Pinnacle(league=league)

    print('Getting Pinnacle Lines...')
    pinny.get_data()

    dkng = draftkings.DraftKings(
        league=league, 
        category_id=4606
    )

    print('Getting DraftKings Lines...')
    dkng.get_data()

    pb = pointsbet.PointsBet()
    print('Getting PointsBet Lines...')
    
    pb.get_data()
    
    print('Getting Caesers Lines...')
    czr = caesers.Caesers()
    czr.get_data()
    
    print('Getting BetMGM Lines...')
    mgm = betmgm.BetMGM()
    mgm.get_data()

    print('Returning ROI Calculations:')

    retail = (
        dkng.df
        .assign(
            DraftKings = lambda x: x['price'].apply(Calculator.convert_american_to_decimal)
        )
        [['participant_name', 'points', 'DraftKings']]
        .merge(
            (
                pb.df
                .rename(columns={'odds_decimal': 'PointsBet'})
            )
        )
        .merge(
            (
                czr.df
                .rename(columns={'price': 'Caesers'})
            )
        )
        .merge(
            (
                mgm.df
                .rename(columns={'price': 'BetMGM'})
            )
        )   
        .melt(
            id_vars=['participant_name', 'points'],
            var_name='book',
            value_name='Decimal Odds'
        )
    )

    ROI = (
        pinny.df
        .assign(
            raw_probability = lambda x: x['price'].apply(Calculator.get_implied_probability),
            vig_free_probability = lambda x: x['raw_probability'] / x.groupby(['matchup_id', 'key'])['raw_probability'].transform('sum')
        )
        [['participant_name', 'points', 'price', 'vig_free_probability']]
        .merge(
            retail,
            on=['participant_name', 'points'],
            how='left'
        )
        .assign(
            ROI = lambda x: round(100 * (x['Decimal Odds'] * x['vig_free_probability'] - 1),1),
            AmericanOdds = lambda x: round(x['Decimal Odds'].apply(Calculator.convert_decimal_to_american))
        )
        .sort_values(
            by='ROI',
            ascending=False
        )
        .head(15)
    )


    print(right_now())
    print(ROI.to_markdown(index=False))

if __name__ == "__main__":
    main()