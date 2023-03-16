import argparse
import pendulum
import sys
sys.path.append('..')

from sportsbooks import (
    pinnacle,
    pointsbet,
    draftkings,
    caesers,
    betmgm,
    betrivers,
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
    parser.add_argument("--league", default="NBA", help="Choose sports league for which to collect data; e.g. NBA, NCAA, etc")
    parser.add_argument("--verbose", default=True, help="If True, show all retail prices for top ROI bet suggested")
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

    mgm = betmgm.BetMGM(league=args.league)
    print('Getting BetMGM Lines...')
    mgm.get_data()

    kambi = betrivers.BetRivers(league=args.league)
    print('Getting BetRivers...')
    kambi.get_data()

    print('Returning ROI Calculations:')

    pricing_spine = (
        pinny.df
        .query('is_live == False')
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
        .merge(
            mgm.df.rename(columns={'price': 'BetMGM'}),
            how='outer',
            on=['participant_name', 'points']
        )
        .merge(
            kambi.df.rename(columns={'price': 'BetRivers'}),
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

    if args.verbose:
        show_all_retail_books(ROI, retail_books)

def show_all_retail_books(ROI, retail_books):
    '''
    Show all retail book prices for top-ROI bet.
    '''

    if ROI.shape[0] == 0:
        print(f"There are no lines.")

    else:

        participant_name = ROI.to_dict('records')[0]['participant_name']
        points = ROI.to_dict('records')[0]['points']

        print(
            retail_books
            .query(f"participant_name == '{participant_name}'")
            .query(f'points == {points}')
            .assign(
                price = lambda x: x['Decimal Odds'].apply(Calculator.convert_decimal_to_american).transform(lambda s: round(s))
            )
            .sort_values(
                by='Decimal Odds',
                ascending=False
            )
            .to_markdown(index=False)
        )

if __name__ == "__main__":
    main()
