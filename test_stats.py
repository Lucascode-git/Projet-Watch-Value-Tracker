# 1: Imports
from numpy import std
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np


from app import get_history, compute_stats

stats = compute_stats(get_history('rolex-daytona-126500ln'))

assert stats['current_price'] == 28250
assert stats['change_12m'] == -4.4
assert stats['change_total'] == -27.8
assert stats['premium'] == 76.6
assert stats['yearly_volatility'] == 9.0
print('All checks passed')


def simulate_purchase(history, date, paid):
    compute_stats = {}

    date_purchase = history['date'] == date
    price_market = history['price'].to_numpy()[-1]
    price_purchase_month = history.loc[date_purchase, 'price'].to_numpy()[0]
    
    compute_stats['market_price_then'] = int(price_purchase_month)
    compute_stats['gap_to_market'] = round(float((paid - price_purchase_month) / price_purchase_month *100),1)
    compute_stats['current_price'] = int(price_market)
    compute_stats['gain'] = int(price_market - paid)
    compute_stats['gain_percent'] = round(float((price_market - paid) / paid *100),1)
    return compute_stats

print(simulate_purchase(get_history('rolex-daytona-126500ln'), '2022-03', 42000))