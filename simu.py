import os 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt

file = pd.read_csv('watchprices.csv')

def get_history(slug):
    """ Return a pandas DataFrame with all columns for one watch, sorted by date """
    line = file['slug'] == slug
    file['date'] = pd.to_datetime(file['date'])
    datas_days = file.loc[line, :]
    return datas_days.sort_values('date', ascending=True)

def compute_stats(history):
    dict_data_model = {}
    current_price = history['price']
    current_price = current_price.iloc[-1]
    dict_data_model['current_price'] = float(current_price)

    min_price = history['price'].min()
    dict_data_model['min_price'] = float(min_price)
    max_price = history['price'].max()
    dict_data_model['max_price'] = float(max_price)

    if len(history['price']) >= 13: 
        index_period = 13
        last12months = (history['price'].iloc[-1] - history['price'].iloc[-index_period]) / history['price'].iloc[-index_period] *100
        dict_data_model['variation_12m'] = round(float(last12months),1)
    else :
        dict_data_model['variation_12m'] = None

    totalvariation = (history['price'].iloc[-1] - history['price'].iloc[0]) / history['price'].iloc[0] *100
    dict_data_model['all_variation'] = round(float(totalvariation),1)

    prime = (history['price'].iloc[-1] - history['retail_price'].iloc[0]) / history['retail_price'].iloc[0] *100
    dict_data_model['prime'] = round(float(prime),1)

    price_np = np.array(history['price'])
    diff_price = np.diff(price_np)
    startvalue = price_np[:-1]
    np_monthly_var = diff_price / startvalue * 100
    yearly_vol = np_monthly_var.std() * (np.sqrt(12))
    dict_data_model['annual_vol'] = round(float(yearly_vol),1)

    return dict_data_model

#print(get_history('rolex-daytona-126500ln'))
#print()
#print(compute_stats(get_history('rolex-daytona-126500ln')))
#print(type(file['date'][0]))

def chart(history):
    date_prices = history['date'].to_numpy()
    prices_watch = history['price'].to_numpy()
    retail_price = history['retail_price'].to_numpy()[0]
    
    plt.figure(figsize=(9, 4))
    plt.plot(date_prices, prices_watch, label='Market price')
    plt.axhline(retail_price, linestyle='--', label='Retail price', color='gray')
    plt.legend()
    plt.xticks(date_prices[::6], rotation=45)
    plt.show()

print(chart(get_history('rolex-daytona-126500ln')))