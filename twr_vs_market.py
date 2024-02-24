import json
import csv
from datetime import datetime
import requests
import configparser
import matplotlib.pyplot as plt


def main(symbols, apikey, output_size='compact', use_cached_response=False, dir_data=''):
    with open(dir_data + 'invest_data.json') as f:
        data = json.load(f)['lines'][0]['dataPoints'][2:]

    market_data = None
    if use_cached_response:
        with open(dir_data + 'market_data.json') as f:
            market_data = json.load(f)
    else:
        market_data = dict.fromkeys(symbols)

        for symbol in market_data.keys():
            market_data[symbol] = get_api_data(symbol, apikey, output_size)

    process_data(data, market_data)
    return

def get_api_data(symbol, apikey, output_size):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize={output_size}&symbol={symbol}&apikey={apikey}'
    response = requests.get(url).json()

    with open(dir_data + 'market_data.json', 'w') as f:
        json.dump(response, f)

    return response

def process_data(data, market_data):
    twr = 1.0
    for i, row in enumerate(data):
        date = row['timestamp'][:10]    # remove time + timezone
        if (i > 0):
            daily_gain = (row['change'] - data[i-1]['change']) / row['value']
            twr *= (1 + daily_gain)
        row['timestamp'] = date
        row['TWR'] = twr

        for symbol in market_data.keys():
            start_price = float(market_data[symbol]['Time Series (Daily)'][data[0]['timestamp']]['4. close'])
            row[symbol] = float(market_data[symbol]['Time Series (Daily)'][date]['4. close']) / start_price

    x = [datetime.strptime(row['timestamp'], "%Y-%m-%d") for row in data]
    plt.plot(x, [row['TWR'] for row in data], label='TWR', drawstyle='steps-post')
    for symbol in market_data.keys():
        plt.plot(x, [row[symbol] for row in data], label=symbol, drawstyle='steps-post')
    
    plt.legend()
    plt.yscale('log')
    plt.show()

    with open('Random/Sofi/data/vs_market_output.csv', 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, ['timestamp', 'value', 'change', 'TWR'] + list(market_data.keys()) , extrasaction='ignore')
        dict_writer.writeheader()
        dict_writer.writerows(data)

    return

if __name__ == "__main__":
    cfg = configparser.ConfigParser()
    cfg.read('Random/Sofi/data/default.cfg')
    apikey = cfg.get('KEYS', 'api_key', raw='')
    output_size = cfg.get('SETTINGS', 'output_size', raw='')
    symbols = cfg.get('SETTINGS', 'symbols', raw='').split(',')
    use_cached_response = cfg.get('SETTINGS', 'use_cached_response', raw='').lower() == 'true'
    dir_data = cfg.get('ENVIRONMENT', 'dir_data', raw='')

    main(symbols, apikey, output_size, use_cached_response, dir_data)
