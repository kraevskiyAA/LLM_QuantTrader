import pandas as pd
import numpy as np
from blackscholes import BlackScholesPut, BlackScholesCall

import warnings
warnings.filterwarnings('ignore')


def BlackSholes(S, K, T, r, sigma, type):
    if type == 'call':
        return BlackScholesCall(S=S, K=K, T=T, r=r, sigma=sigma, q=0).price()
    elif type == 'put':
        return BlackScholesPut(S=S, K=K, T=T, r=r, sigma=sigma, q=0).price()
    
    
def BlackSholesDelta(S, K, T, r, sigma, type):
    if type == 'call':
        return BlackScholesCall(S=S, K=K, T=T, r=r, sigma=sigma, q=0).delta()
    elif type == 'put':
        return BlackScholesPut(S=S, K=K, T=T, r=r, sigma=sigma, q=0).delta()
    
    
def get_BS_market_prices(Asset_df, volatility_df, rates_df, strikes, tenors, type = 'vanilla'):

    Asset_df, volatility_df, rates_df  = Asset_df.copy(), volatility_df.copy(), rates_df.copy()

    Asset_df['Date'] = pd.to_datetime(Asset_df['Date'])
    volatility_df['Date'] = pd.to_datetime(volatility_df['Date'])
    rates_df['Date'] = pd.to_datetime(rates_df['Date'])

    rates_df.fillna(method='ffill', inplace = True)

    # exclude trading days with missing values
    volatility_df = volatility_df[volatility_df.Date.isin(Asset_df.Date)].reset_index(drop = True)
    volatility_df = volatility_df[volatility_df.Date.isin(rates_df.Date)].reset_index(drop = True)
    Asset_df = Asset_df[Asset_df.Date.isin(volatility_df.Date)].reset_index(drop = True)
    Asset_df = Asset_df[Asset_df.Date.isin(rates_df.Date)].reset_index(drop = True)
    rates_df = rates_df[rates_df.Date.isin(volatility_df.Date)].reset_index(drop = True)
    rates_df = rates_df[rates_df.Date.isin(Asset_df.Date)].reset_index(drop = True)

    res_df = Asset_df.copy()
    res_df = res_df.merge(volatility_df, on = 'Date', how = 'left')
    res_df = res_df.merge(rates_df, on = 'Date', how = 'left')

    for t in tenors:
        for s in strikes:
            if type == 'vanilla':
                res_df[f'BS_opt_t{t}_s{s}_call'] = res_df.apply(lambda x: BlackSholes(x['SnP500'], s, t/12, x[t]/100, x['VIX']/100, 'call'), axis = 1)
                res_df[f'BS_opt_t{t}_s{s}_put'] = res_df.apply(lambda x: BlackSholes(x['SnP500'], s, t/12, x[t]/100, x['VIX']/100, 'put'), axis = 1)
            else:
                raise Exception('Not yet implemented.')

    res_df = res_df.drop(columns = rates_df.columns[1:])
    return res_df


def get_BS_market_delta(Asset_df, volatility_df, rates_df, strikes, tenors, type = 'vanilla'):

    Asset_df, volatility_df, rates_df  = Asset_df.copy(), volatility_df.copy(), rates_df.copy()

    Asset_df['Date'] = pd.to_datetime(Asset_df['Date'])
    volatility_df['Date'] = pd.to_datetime(volatility_df['Date'])
    rates_df['Date'] = pd.to_datetime(rates_df['Date'])

    rates_df.fillna(method='ffill', inplace = True)

    volatility_df = volatility_df[volatility_df.Date.isin(Asset_df.Date)].reset_index(drop = True)
    volatility_df = volatility_df[volatility_df.Date.isin(rates_df.Date)].reset_index(drop = True)
    Asset_df = Asset_df[Asset_df.Date.isin(volatility_df.Date)].reset_index(drop = True)
    Asset_df = Asset_df[Asset_df.Date.isin(rates_df.Date)].reset_index(drop = True)
    rates_df = rates_df[rates_df.Date.isin(volatility_df.Date)].reset_index(drop = True)
    rates_df = rates_df[rates_df.Date.isin(Asset_df.Date)].reset_index(drop = True)

    res_df = Asset_df.copy()
    res_df = res_df.merge(volatility_df, on = 'Date', how = 'left')
    res_df = res_df.merge(rates_df, on = 'Date', how = 'left')

    for t in tenors:
        for s in strikes:
            if type == 'vanilla':
                res_df[f'BS_opt_t{t}_s{s}_call'] = res_df.apply(lambda x: BlackSholesDelta(x['SnP500'], s, t/12, x[t]/100, x['VIX']/100, 'call'), axis = 1)
                res_df[f'BS_opt_t{t}_s{s}_put'] = res_df.apply(lambda x: BlackSholesDelta(x['SnP500'], s, t/12, x[t]/100, x['VIX']/100, 'put'), axis = 1)
            else:
                raise Exception('Not yet implemented.')

    res_df = res_df.drop(columns = rates_df.columns[1:])
    return res_df


def create_deals(SnP_data, 
                 date_start, 
                 date_end, 
                 n_deals,
                 mu = 10,
                 var = 50,
                 volumes = [1],
                 tenors = [6,12,24],
                 strikes = [500, 1000, 1500],
                 deals = ['buy'],
                 opt_type = ['Call']):
    
    df_opts = pd.DataFrame()

    df_opts['date_open'] = np.random.choice(pd.date_range(date_start, date_end), n_deals, replace = False)
    df_opts['tenors'] = np.random.choice(tenors, n_deals, replace=True)
    df_opts['date_close'] = df_opts.apply(lambda x: x['date_open'] + pd.DateOffset(x['tenors']*30), axis=1)
    df_opts['strikes'] = np.random.choice(strikes, n_deals, replace=True)
    df_opts['deals'] = np.random.choice(deals, n_deals, replace=True)
    df_opts['opt_type'] = np.random.choice(opt_type, n_deals, replace=True)

    df_opts['volumes'] = np.random.choice(volumes, n_deals, replace=True)
    df_opts.sort_values('date_open').reset_index(drop = True)

    SnP_data['Date'] = pd.to_datetime(SnP_data['Date'])
    df_opts = df_opts.merge(SnP_data.rename(columns = {'Date' : 'date_close',
                                                     'SnP500' : 'price'}), on = 'date_close', 
                                                     how = 'left')
    df_opts['price'] -= df_opts['strikes']
    df_opts['price'] -= np.random.normal(mu, var, df_opts.shape[0])
    
    return df_opts.sort_values('date_open').dropna().reset_index(drop = True)