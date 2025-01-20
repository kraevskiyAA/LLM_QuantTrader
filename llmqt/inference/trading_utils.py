import pandas as pd
import numpy as np
from datetime import timedelta
# from collections.abc import isinstance
import matplotlib.pyplot as plt

class trading_agent:

    def __init__(self, start_balance, SnP_data):

        """
        Desctiption
        """

        self.balance = start_balance
        self.relevant_deals = {}
        self.expired_deals = {}
        self.all_deals = {}
        self.SnP_data = SnP_data.copy()
        try:
            self.SnP_data['Date'] = pd.to_datetime(self.SnP_data['Date'])
        except:
            raise Exception('column "Date" not in SnP_data columns.')
        self.current_date = None

    def __check_expired_deals(self):

        """
        Automatic completion of expired options.
        """

        keys_to_del = []

        for d, k in self.relevant_deals.items():
            deal_date = pd.to_datetime(k['Deal Expire'])
            if deal_date <= self.current_date and k['Deal'] == 'Buy':
                self.expired_deals[d] = k
                self.all_deals[d] = k
                self.all_deals[d]['Deal'] = 'Exercise'
                current_price = self.SnP_data[self.SnP_data.Date == deal_date]['SnP500'].values[0]
                deal_price =  k['Strike']
                if k['Option Type'] == 'Put':
                    PnL = max(0, k['Amount']*(deal_price - current_price))
                elif k['Option Type'] == 'Call':
                    PnL = max(0, k['Amount']*(current_price - deal_price)) 
                else:
                    raise Exception('Inappropriate option type, must be either "Call" or "Put".')
                print('Option type:', k['Option Type'], f', PnL: {PnL}', 'Strike:', k['Strike'], 'current price:', current_price, 'Option price:', k['Price'])
                self.balance += PnL
                keys_to_del.append(d)
            
        self.relevant_deals = {key: self.relevant_deals[key] for key in self.relevant_deals.keys() if key not in keys_to_del}


    def buy(self, time, price, n_options, opt_type, strike, term, delta = None, **kwargs):

        if not isinstance(n_options, int):
            raise Exception(f'n_options parameter must be integer, not {type(n_options)}.')

        # Set starting time equal to the time of first deal
        if self.current_date is None:
            self.current_date = pd.to_datetime(time)
        else:
            if self.current_date > pd.to_datetime(time):
                raise Exception('New deals cannot be made in the past (time lower then time for the previous one).')
            else:
                self.current_date = pd.to_datetime(time)

        deal = {
                'Deal' : 'Buy',
                'Deal Open' : pd.to_datetime(time),
                'Deal Expire' : pd.to_datetime(time) + timedelta(days = term * 30),
                'Price' : price,
                'Amount' : n_options,
                'Option Type' : opt_type,
                'Strike' : strike,
                'Term' : term,
                'Delta' : delta
                }
        
        if deal['Amount'] * deal['Price'] > self.balance:
            raise Exception(f"Current balance doesn't allow you make this deal. Your balance: {round(self.balance, 2)}, required amount: {round(deal['Amount'] * deal['Price'], 2)}")
        else:
            self.balance -= deal['Amount'] * deal['Price']
        
        if f'Date{time[:10]}_Strike{strike}_Term{term}_Opt{opt_type}_DealBuy' in self.relevant_deals.keys():
            raise Exception('Similar deal has been already made, please check the relevant list of deals.')
        else:
            self.relevant_deals[f'Date{time[:10]}_Strike{strike}_Term{term}_Opt{opt_type}_DealBuy'] = deal
            self.all_deals[f'Date{time[:10]}_Strike{strike}_Term{term}_Opt{opt_type}_DealBuy'] = deal

        self.__check_expired_deals()

    def sell(self, time, price, n_options, opt_type, strike, term, delta = None, **kwargs):

        if f'Date{time[:10]}_Strike{strike}_Term{term}_Opt{opt_type}_DealBuy' in self.relevant_deals.keys():
            pass
        else:
            raise Exception('No such deal, check the correctness of your inputs.')
        

        if self.current_date is None:
            self.current_date = pd.to_datetime(time)
        else:
            if self.current_date > pd.to_datetime(time):
                raise Exception('New deals cannot be made in the past (time lower then time for the previous one).')
            else:
                self.current_date = pd.to_datetime(time)

        deal = {
                'Deal' : 'Sell',
                'Deal Open' : pd.to_datetime(time),
                'Deal Expire' : pd.to_datetime(time) + timedelta(days = term * 30),
                'Price' : price,
                'Amount' : n_options,
                'Option Type' : opt_type,
                'Strike' : strike,
                'Term' : term,
                'Delta' : delta
                }

        if n_options < self.relevant_deals[f'Date{time[:10]}_Strike{strike}_Term{term}_Opt{opt_type}_DealBuy']['Amount']:
            self.relevant_deals[f'Date{time[:10]}_Strike{strike}_Term{term}_Opt{opt_type}_DealBuy']['Amount'] -= n_options
        elif n_options == self.relevant_deals[f'Date{time[:10]}_Strike{strike}_Term{term}_Opt{opt_type}_DealBuy']['Amount']:
            del self.relevant_deals[f'Date{time[:10]}_Strike{strike}_Term{term}_Opt{opt_type}_DealBuy']
        else:
            raise Exception("Amount of options sold can't be greater then the purchased amount.")
        
        self.all_deals[f'Date{time[:10]}_Strike{strike}_Term{term}_Opt{opt_type}_DealSell'] = deal
        self.balance += deal['Amount'] * deal['Price']
    
        self.__check_expired_deals()

def calc_weighted_avg_delta(agent):

    full_position = 1e-10
    deltas = []
    for _, deal in agent.relevant_deals.items():
        if not (deal['Delta'] is None or np.isnan(deal['Delta'])):
            weight_factor = deal['Amount'] * deal['Price']
            deltas.append(deal['Delta'] * weight_factor)
            full_position += weight_factor
        else:
            pass
    try:
        return sum(deltas) / full_position
    except:
        return np.nan
    

def calc_Sharpe_ratio(agent, rf_rate_df, SnP_df, volatility_df):

    full_position = 1e-10
    returns_opt = []
    returns_rf = []
    implied_vol = []
    for _, deal in agent.relevant_deals.items():
        weight_factor = deal['Amount'] * deal['Price']
        deal_date = pd.to_datetime(deal['Deal Expire'])
        deal_start = pd.to_datetime(deal['Deal Open'])
        if deal_start in volatility_df.Date.unique() and deal_start in rf_rate_df.Date.unique():
            # print('Successfully found required date!')
            # print(len(SnP_df))
            current_price = SnP_df[SnP_df.Date == deal_date]['SnP500'].values[0] # No matching strings (WTF???)
            # print(current_price)
            Term = deal['Term']
            if deal['Option Type'] == 'Put':
                PnL = max(0, (deal['Strike'] - current_price - deal['Price'])) / deal['Price']
            elif deal['Option Type'] == 'Call':
                PnL = max(0, (current_price - deal['Strike'] - deal['Price'])) / deal['Price']
            returns_opt.append(PnL * weight_factor)
            returns_rf.append(rf_rate_df[rf_rate_df.Date == deal_start][f'{Term}'].values[0] * weight_factor)
            implied_vol.append(volatility_df[volatility_df.Date == deal_start]['VIX'].values[0] * weight_factor)
            full_position += weight_factor

            # print('!')
            # print(volatility_df[volatility_df.Date == deal_date]['VIX'].values[0])
            # print(rf_rate_df[rf_rate_df.Date == deal_start][f'{Term}'].values[0])
            # print(PnL)

        else:
            pass

    avg_return_opt = sum(returns_opt) / full_position
    avg_return_rf = sum(returns_rf) / full_position
    volatility = sum(implied_vol) / full_position

    try:
        return (avg_return_opt - avg_return_rf) / volatility
    except:
        return np.nan

def adjust_market_deltas(delta, deals):

    deals_deltas = []

    delta, deals = delta.copy(), deals.copy()
    delta['Date'], deals['date_open'] = pd.to_datetime(delta['Date']), pd.to_datetime(deals['date_open'])
    deals['deal_shortname'] = pd.Series(['BS_opt_t'] * len(deals)) + deals['tenors'].astype(str) + '_s' + deals['strikes'].astype(str) +'_' + deals['opt_type'].str.lower()

    delta.set_index(delta['Date'], inplace=True)

    for i in range(len(deals)):
        try:
            deal_str = delta.loc[deals['date_open'][i]]
            deals_deltas.append(deal_str[deals['deal_shortname'][i]])
        except:
            deals_deltas.append(None)

    deals['delta'] = deals_deltas

    return deals


def add_all_deals(agent, 
                  deals_df,
                  rf_rate_df, 
                  SnP_df, 
                  volatility_df):

    deals_df = deals_df.copy()
    deals_df.rename(columns = {
    'date_open' : 'time',
    'volumes' : 'n_options',
    'strikes' : 'strike',
    'tenors' : 'term'
        }, inplace = True)
    
    deals_df['time'] = deals_df['time'].astype(str).apply(lambda x: x[:10])
    deals_df['date_close'] = deals_df['date_close'].astype(str).apply(lambda x: x[:10])

    balance, dates, deltas, Sharpes = [], [], [], []

    for i in range(len(deals_df)):

        try:
            if deals_df.iloc[i]['price'] < 0:
                pass
            else:
                agent.buy(**deals_df.iloc[i].to_dict())
                balance.append(agent.balance)
                dates.append(agent.current_date)
                deltas.append(calc_weighted_avg_delta(agent))
                Sharpes.append(calc_Sharpe_ratio(agent, rf_rate_df, SnP_df, volatility_df))
        except:
            pass

    # add the last fake deal to exercise all previous
    fake_deal = deals_df.iloc[-1]
    fake_deal['time'] = '2100-12-31'
    fake_deal['n_options'] = 0
    dates.append(agent.current_date + timedelta(days=1))
    agent.buy(**fake_deal.to_dict())
    balance.append(agent.balance)
    deltas.append(calc_weighted_avg_delta(agent))
    Sharpes.append(calc_Sharpe_ratio(agent, rf_rate_df, SnP_df, volatility_df))


    return balance, dates, deltas, Sharpes

def get_linear_plots_balance(ts, path, label, dates = None, starting_value = None):

    figure = plt.figure()
    if dates is None:
        plt.plot(np.array(ts) / ts[0] * 100, color = 'blue', label = f'{label} (%)')
    else:
        plt.plot(dates, np.array(ts) / ts[0] * 100, color = 'blue', label = f'{label} (%)')
    if starting_value is not None:
        plt.axhline(starting_value, label = 'Starting balance', color = 'red', linestyle = '--')
    plt.grid(alpha = 0.25)
    plt.legend()
    plt.savefig(path+ '/' + label + '.png')

def get_linear_plots_deltas(ts, path, label, dates = None):

    figure = plt.figure()
    if dates is None:
        plt.plot(np.array(ts), color = 'blue', label = f'{label} (%)')
    else:
        plt.plot(dates, np.array(ts), color = 'blue', label = f'{label} (%)')
    plt.axhline(0, label = 0, color = 'red', linestyle = '--')
    plt.grid(alpha = 0.25)
    plt.legend()
    plt.savefig(path+ '/' + label + '.png')

