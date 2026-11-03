# 1: Imports ------------
from flask import request
from flask import url_for
from flask import abort
from flask import render_template
from numpy import std
from flask import Flask
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import numpy as np

# 2: The app -------------
app = Flask(__name__)

# 3: data, loaded once at startup ----------
DATA_WATCHES = os.path.join(app.root_path, 'watch_prices.csv')
prices = pd.read_csv(DATA_WATCHES)

# 4: functions ----------------
def get_history(slug):
    """ Return a pandas DataFrame with all columns for one watch, sorted by date """
    rows_slug = prices['slug'] == slug
    data_day_price = prices.loc[rows_slug, :].sort_values('date', ascending=True)
    return data_day_price

def compute_stats(history):
    """ Return a dict of price statistics for one watch: current, min, max, 12-month and total change, premium over retail, annualized volatility """
    dict_data_price = {}
    data_price = history['price'].to_numpy()
    data_retail_price = history['retail_price'].to_numpy()[0]

    dict_data_price['current_price'] = int(data_price[-1])
    dict_data_price['minimum_price'] = int(data_price.min())
    dict_data_price['maximum_price'] = int(data_price.max())
    dict_data_price['change_12m'] = round(float((data_price[-1] - data_price[-13])/data_price[-13]*100),1)
    dict_data_price['change_total'] = round(float((data_price[-1] - data_price[0])/data_price[0]*100),1)
    dict_data_price['premium'] = round(float((data_price[-1] - data_retail_price)/data_retail_price*100),1)

    monthly_return = np.diff(data_price) / data_price[:-1]
    volatility = np.std(monthly_return) * np.sqrt(12)
    dict_data_price['yearly_volatility'] = round(float(volatility * 100),1)
    return dict_data_price

def make_chart(history, slug):
    date_prices = history['date'].to_numpy()
    prices_watch = history['price'].to_numpy()
    retail_price = history['retail_price'].to_numpy()[0]
    
    plt.figure(figsize=(9, 4))
    plt.plot(date_prices, prices_watch, label='Market price')
    plt.axhline(retail_price, linestyle='--', label='Retail price', color='gray')
    plt.legend()
    plt.xticks(date_prices[::6], rotation=45)
    

    charts_folder = os.path.join(app.root_path, 'static', 'charts')
    os.makedirs(charts_folder, exist_ok=True)
    chart_path = os.path.join(charts_folder, f'{slug}.png')
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    return f'charts/{slug}.png'

def simulate_purchase(history, date, paid):
    """Compare the price paid with the market price at purchase and today, return a dict of numbers."""
    simulation = {}

    date_purchase = history['date'] == date
    current_price = history['price'].to_numpy()[-1]
    price_purchase_month = history.loc[date_purchase, 'price'].to_numpy()[0]
    
    simulation['market_price_then'] = int(price_purchase_month)
    simulation['gap_to_market'] = round(float((paid - price_purchase_month) / price_purchase_month *100),1)
    simulation['current_price'] = int(current_price)
    simulation['gain'] = int(current_price - paid)
    simulation['gain_percent'] = round(float((current_price - paid) / paid *100),1)
    return simulation
    

# 5: Routes -----------------
@app.route('/')
def home():
    watches = []
    for slug in prices['slug'].unique():
        history = get_history(slug)
        stats = compute_stats(history)
        watches.append({
            'slug': slug,
            'brand': history['brand'].to_numpy()[0],
            'model': history['model'].to_numpy()[0],
            'current_price_display': f"{stats['current_price']:,}",
            'change_12m': stats['change_12m'],
            'change_total': stats['change_total'],
        })
    return render_template('home.html', watches=watches, title='Home')

@app.route('/about')
def about():
    return render_template('about.html', title= 'About')

@app.route('/simulate', methods=['GET', 'POST'])
def simulate():
    watches = []
    for slug in prices['slug'].unique():
        history = get_history(slug)
        watches.append({
            'slug': slug,
            'brand': history['brand'].to_numpy()[0],
            'model': history['model'].to_numpy()[0],
        })
    months = sorted(prices['date'].unique())

    # 1. First visit: empty form
    if request.method == 'GET':
        return render_template('simulate.html', watches=watches, months=months, title='Simulate')

    # 2. Form submitted: read the fields
    slug = request.form['slug']
    date = request.form['date']

    # 3. Convert the price, or show an error
    try:
        paid = float(request.form['paid'])
    except ValueError:
        return render_template('simulate.html', watches=watches, months=months, title='Simulate',
                               error='Enter a number')

    # 4. Compute
    history = get_history(slug)
    result = simulate_purchase(history, date, paid)

    result['paid_display'] = f"{paid:,.0f}"
    result['market_price_then_display'] = f"{result['market_price_then']:,}"
    result['current_price_display'] = f"{result['current_price']:,}"
    result['gain_display'] = f"{result['gain']:,}"

    # 5. Show the form with the result below
    return render_template('simulate.html', watches=watches, months=months, title='Simulate', result=result)

@app.route('/watch/<slug>')
def watch(slug):
    if slug not in prices['slug'].unique():
        abort(404)
    
    history = get_history(slug)
    stats = compute_stats(history)
    chart = make_chart(history, slug)
    watch_details = {
        'brand': history['brand'].to_numpy()[0],
        'model': history['model'].to_numpy()[0],
        'reference': history['reference'].to_numpy()[0], 
        'current_price': stats['current_price'],
        'current_price_display': f"{stats['current_price']:,}",
        'minimum_price': stats['minimum_price'],
        'minimum_price_display': f"{stats['minimum_price']:,}",
        'maximum_price': stats['maximum_price'],
        'maximum_price_display': f"{stats['maximum_price']:,}",
        'change_12m': stats['change_12m'],
        'change_total': stats['change_total'],
        'premium': stats['premium'],
        'yearly_volatility': stats['yearly_volatility'],
    }
    return render_template('watch.html', watch=watch_details, title=watch_details['model'], chart=chart)

# 6: server start ---------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=5001)




