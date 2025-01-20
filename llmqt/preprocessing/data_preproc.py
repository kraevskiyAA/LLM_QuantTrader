import pandas as pd
import numpy as np 

def preproc_VIX(data_path):

    df = pd.read_csv(data_path)
    df['DATE'] = pd.to_datetime(df['DATE'])

    return df[['DATE', 'OPEN']].rename(columns = {
            'DATE' : 'Date',
            'OPEN' : 'VIX'
            }).sort_values('Date').reset_index(drop = True)


def find_nearest_rate(possible_vals, a0):

    possible_vals = np.sort(np.array(possible_vals))
    idx = np.abs(possible_vals - a0).argmin()
    first_bound = possible_vals.flat[idx]
    
    try:
        if first_bound < a0:
            second_bound = possible_vals.flat[idx+1]
            return first_bound, second_bound
        else:
            second_bound = possible_vals.flat[idx-1]
            return second_bound, first_bound
    except:
        raise Exception('Index can not be greater than the max value of array')

def get_interpolated_rates_df(rate_df, max_tenor = 361, min_tenor = 1):

    rate_df = rate_df.copy()
    present_rates = rate_df.columns[1:].to_list()

    for r in range(min_tenor, max_tenor):
        if r in present_rates:
            pass
        else:
            bound_1, bound_2 = find_nearest_rate(present_rates, r)
            distance_1, distance_2 = (r - bound_1) / (bound_2 - bound_1), (bound_2 - r) / (bound_2 - bound_1)
            rate_df[r] = distance_1 * rate_df[bound_1] + distance_2 * rate_df[bound_2]

    return rate_df

def preproc_rf_rate(data_path):

    rf_rate = pd.read_csv(data_path)
    rf_rate.rename(columns = {
        '1 Mo' : 1,
        '2 Mo' : 2,
        '3 Mo' : 3,
        '4 Mo' : 4,
        '6 Mo' : 6,
        '1 Yr' : 12,
        '2 Yr' : 24,
        '3 Yr' : 36,
        '5 Yr' : 60,
        '7 Yr' : 84,
        '10 Yr' : 120,
        '20 Yr' : 240,
        '30 Yr' : 360
    }, inplace = True)

    rf_rate['Date'] = pd.to_datetime(rf_rate['Date'])
    rf_rate.fillna(method='ffill', inplace = True)

    return get_interpolated_rates_df(rf_rate)


