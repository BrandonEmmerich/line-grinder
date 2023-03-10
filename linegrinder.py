import argparse
import pendulum
import sys
sys.path.append('..')

from sportsbooks import (
    pinnacle,
    pointsbet,
    draftkings,
    caesers,
)

from calculator import Calculator

def right_now():
    """
    Return the current time.
    """
    return str(pendulum.now()).split('.')[0].replace('T', ' ')

def main():
    """
    Find 'Off Market' lines, calculate estimated ROI%.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", default="NBA")
    args = parser.parse_args()
    print(f"Getting data for {args.league}")

    pinny = pinnacle.Pinnacle(league=args.league)
    print('Getting Pinnacle Lines...')
    pinny.get_data()

    pb = pointsbet.PointsBet(league=args.league)
    print('Getting PointsBet Lines...')
    pb.get_data()

    dkng = draftkings.DraftKings(league=args.league)
    print('Getting DraftKings Lines...')
    dkng.get_data()

    czr = caesers.Caesers(league=args.league)
    print('Getting Caesers Lines...')
    czr.get_data()

    print('Returning ROI Calculations:')

    pricing_spine = (
        pinny.df
        .assign(
            raw_probability = lambda x: x['price'].apply(Calculator.get_implied_probability),
            vig_free_probability = lambda x: x['raw_probability'] / x.groupby(['matchup_id', 'key'])['raw_probability'].transform('sum')
        )
        [['participant_name', 'points', 'price', 'vig_free_probability']]
    )

    retail_books = (
        pb.df.rename(columns={'price': 'PointsBet'})
        .merge(
            dkng.df.rename(columns={'price': 'DraftKings'}),
            how='outer',
            on=['participant_name', 'points']
        )
        .merge(
            czr.df.rename(columns={'price': 'Caesers'}),
            how='outer',
            on=['participant_name', 'points']
        )
        .melt(
            id_vars=['participant_name', 'points'],
            var_name='book',
            value_name='Decimal Odds'
        )
    )

    ROI = (
        pricing_spine
        .merge(
            retail_books,
            on=['participant_name', 'points'],
            how='left'
        )
        .assign(
            BookPrice = lambda x: round(x['Decimal Odds'].apply(Calculator.convert_decimal_to_american)),
            roi = lambda x: round(100 * (x['Decimal Odds'] * x['vig_free_probability'] - 1),1),
            ROI = lambda x: x['roi'].transform(lambda s: f'{s}%'),
            vig_free_probability = lambda x: x['vig_free_probability'].transform(lambda s: f'{round(100 * s, 1)}%')
        )
        .sort_values(
            by='roi',
            ascending=False
        )
        [['participant_name', 'points', 'price', 'vig_free_probability', 'book', 'BookPrice', 'ROI']]
    )

    print(right_now())
    print(ROI.head(15).to_markdown(index=False))

if __name__ == "__main__":
    main()
