import hydra
from omegaconf import DictConfig, OmegaConf

import pandas as pd
import logging
import numpy as np

from llmqt.inference.trading_utils import *
from llmqt.preprocessing.data_preproc import * 
from llmqt.preprocessing.BS_pricing import * 


import warnings
warnings.filterwarnings('ignore')


@hydra.main(config_path="./config", config_name="TradeConf.yaml")

def main(config: DictConfig):

    logger = logging.getLogger("experiment")
    
    OmegaConf.resolve(config)
    logger.info(OmegaConf.to_yaml(config))
    logger.info("RUN "+config["name"]+" EXPERIMENT")
    logger.info("Upload required data...")

    SnP_df = pd.read_csv(config['datapaths']['SnP_path'])
    rf_rate_df = preproc_rf_rate(config['datapaths']['rf_rate_path'])
    VIX_df = preproc_VIX(config['datapaths']['VIX_path'])

    logger.info("Success!")
    logger.info('Creating dataset with option prices and deltas...')
    
    prices_df = get_BS_market_prices(Asset_df = SnP_df, 
                                        volatility_df = VIX_df, 
                                        rates_df = rf_rate_df, 
                                        strikes = config['simulated_deals']['strikes'], 
                                        tenors =  config['simulated_deals']['tenors'])
    
    delta_df = get_BS_market_delta(Asset_df = SnP_df, 
                                    volatility_df = VIX_df, 
                                    rates_df = rf_rate_df, 
                                    strikes = config['simulated_deals']['strikes'], 
                                    tenors =  config['simulated_deals']['tenors'])

    logger.info("Success!")
    logger.info('Sampling simulated deals...')

    # Here must be an LLM
    deals = create_deals(SnP_data = SnP_df, 
            date_start = config['simulated_deals']['date_start'], 
            date_end = config['simulated_deals']['date_end'], 
            n_deals = config['simulated_deals']['n_deals'],
            mu = config['simulated_deals']['mu'],
            var = config['simulated_deals']['var'],
            volumes = config['simulated_deals']['volumes'],
            tenors = config['simulated_deals']['tenors'],
            strikes = config['simulated_deals']['strikes'],
            deals = config['simulated_deals']['deals'],
            opt_type = config['simulated_deals']['opt_type']
            )
    
    # Just for debugging
    deals.to_csv('/Users/artyomkraevskiy/Desktop/RPD paper/Trading_agent/deals_for_debug.csv', index = None)

    logger.info("Success!")
    logger.info('Add market deltas...')

    deals = adjust_market_deltas(delta_df, deals)

    logger.info("Success!")
    logger.info("Setting trading agent...")

    agent = trading_agent(config['agent']['start_balance'], SnP_df)

    logger.info("Success!")
    logger.info("Execute all simulated deals...")

    balances, dates, delta, Sharpes = add_all_deals(agent, 
                                           deals,
                                           rf_rate_df, 
                                           SnP_df, 
                                           VIX_df)

    logger.info("All deals have been succefully executed!")
    logger.info("Plotting...")

    get_linear_plots_balance(balances, config['plots']['saving_path'], 'Balance', dates, 100)
    get_linear_plots_deltas(delta, config['plots']['saving_path'], 'Avg portfolio delta', dates)
    # get_linear_plots_deltas(delta, config['plots']['saving_path'], 'Sharpe ratio', dates)


    logger.info("Success!")

if __name__ == "__main__":   
    main()