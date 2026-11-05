# 1: Imports ------------
from numpy import append
from flask import request
from flask import abort
from flask import render_template
from flask import Flask
import os 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
import matplotlib
matplotlib.use('Agg')


# 2: The app -------------
app = Flask(__name__)


# 3: data, loaded once at startup ----------
DATA_WATCHES = os.path.join(app.root_path, 'watchprices.csv') #allows to acces file outside folder
file = pd.read_csv(DATA_WATCHES)


# 4: functions
def get_history(slug):
    line = file['slug'] == slug
    file['date'] = pd.to_datetime(file['date'])
    dataslug = file.loc[line, :]
    return dataslug.sort_values('date', ascending=True)


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


def create_charts(history, slug):
    date_prices = history['date'].to_numpy()
    prices_watch = history['price'].to_numpy()
    retail_price = history['retail_price'].to_numpy()[0]
    
    plt.figure(figsize=(9, 4))
    plt.plot(date_prices, prices_watch, label='Market price')
    plt.axhline(retail_price, linestyle='--', label='Retail price', color='gray')
    plt.legend()
    plt.xticks(date_prices[::6], rotation=45)
    plt.show()

    charts_folder = os.path.join(app.root_path, 'static', 'allcharts')
    os.makedirs(charts_folder, exist_ok=True)
    chart_path = os.path.join(charts_folder, f'{slug}.png')
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    return f'allcharts/{slug}.png'


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
    watch = []
    for slug in file['slug'].unique():
        history = get_history(slug)
        stats = compute_stats(history)
        watch.append({
            'slug': slug,
            'brand': history['brand'].to_numpy()[0],
            'model': history['model'].to_numpy()[0],
            'current_price': stats['current_price'],
            'current_price_display': f"{stats['current_price']:,.0f}",
            'change_12m': stats['variation_12m'],
            'change_total': stats['all_variation'],})

    return render_template('home.html', watch=watch, title='Home')


@app.route('/about')
def about():
    return render_template('about.html', title='About')


@app.route('/simulate', methods=['GET', 'POST'])
def simulate():
    watch = []
    for slug in file['slug'].unique():
        history = get_history(slug)
        watch.append({
            'slug': slug,
            'brand': history['brand'].to_numpy()[0],
            'model': history['model'].to_numpy()[0]
        })
    months = file['date'].dt.strftime('%b-%Y').unique()

    # 1. First visit: empty form
    if request.method == 'GET':
        return render_template('simulate.html', watch=watch, months=months, title='Simulate')
    # 2. Form submitted: read the fields
    slug = request.form['slug']
    date = request.form['date']
    # 3. Convert the price, or show an error
    try:
        paid = float(request.form['paid'])
    except ValueError:
        return render_template('simulate.html', watch=watch, months=months, title='Simulate',
                               error='Enter a number')

    # 4. Compute
    history = get_history(slug)
    result = simulate_purchase(history, date, paid)

    result['paid_display'] = f"{paid:,.0f}"
    result['market_price_then_display'] = f"{result['market_price_then']:,}"
    result['current_price_display'] = f"{result['current_price']:,}"
    result['gain_display'] = f"{result['gain']:,}"
    result['brand'] = history['brand'].to_numpy()[0]
    result['model'] = history['model'].to_numpy()[0]
    result['date'] = date

    # 5. Show the form with the result below
    return render_template('simulate.html', watch=watch, months=months, title='Simulate', result=result)




@app.route('/watch/<slug>')
def watch(slug):
    if slug not in file['slug'].unique():
        abort(404)
    
    history = get_history(slug)
    stats = compute_stats(history)
    chart = create_charts(history, slug)
    watch_details ={
        'brand': history['brand'].to_numpy()[0],
        'model': history['model'].to_numpy()[0],
        'reference': history['reference'].to_numpy()[0], 
        'current_price': stats['current_price'],
        'current_price_display': f'{stats['current_price']:,.0f}',
        'minimum_price': stats['min_price'],
        'minimum_price_display': f'{stats['min_price']:,.0f}',
        'maximum_price': stats['max_price'],
        'maximum_price_display': f'{stats['max_price']:,.0f}',
        'change_12m': stats['variation_12m'],
        'change_total': stats['all_variation'],
        'premium': stats['prime'],
        'yearly_volatility': stats['annual_vol'],
        
    }
    return render_template('watch.html', watch=watch_details, chart=chart, title=watch_details['model'])



# 6: server start ---------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=5001)
