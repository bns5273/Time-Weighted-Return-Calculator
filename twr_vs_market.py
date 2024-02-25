import json
import csv
from datetime import datetime
import requests
import configparser
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates


def main(symbols, apikey, output_size='full', use_cached_response=False, dir_data=''):
    with open(dir_data + 'invest_data.json') as f:
        data = json.load(f)['lines'][0]['dataPoints'][2:]

    market_data = dict.fromkeys(symbols)
    if use_cached_response:
        with open(dir_data + 'market_data.json') as f:
            loaded = json.load(f)
            for symbol in market_data.keys():
                market_data[symbol] = loaded[symbol]
    else:
        for symbol in market_data.keys():
            market_data[symbol] = get_api_data(symbol, apikey, output_size)

        with open(dir_data + 'market_data.json', 'w') as f:
            json.dump(market_data, f)

    process_data(data, market_data)
    return 0

def get_api_data(symbol, apikey, output_size):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize={output_size}&symbol={symbol}&apikey={apikey}'
    response = requests.get(url).json()

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
    y = [100 * row['TWR'] for row in data]
    plt.figure().set_size_inches(12, 6)
    plt.plot(x, y, label='TWR', drawstyle='steps-post', color='black')
    plt.annotate(text=f'TWR: ${round(y[-1], 2)}', 
        xy=(x[-1], y[-1]), 
        xytext=(x[-1], y[-1] + 5), 
        arrowprops=dict(facecolor='black', arrowstyle='->')
    )
    for symbol in market_data.keys():
        y = [100 * row[symbol] for row in data]
        plt.plot(x, y, label=symbol, drawstyle='steps-post', alpha=0.7)
        plt.annotate(text=f'{symbol}: ${round(y[-1], 2)}', 
            xy=(x[-1], y[-1]), 
            xytext=(x[-1], y[-1] + 5), 
            arrowprops=dict(facecolor='black', arrowstyle='->')
        )
        if max(y) > y[-1]:
            plt.annotate(text=f'{symbol}: ${round(max(y), 2)}', 
                xy=(x[y.index(max(y))], max(y)), 
                xytext=(x[y.index(max(y))], max(y) + 5), 
                arrowprops=dict(facecolor='black', arrowstyle='->')
            )
        if min(y) < y[-1]:
            plt.annotate(text=f'{symbol}: ${round(min(y), 2)}', 
                xy=(x[y.index(min(y))], min(y)), 
                xytext=(x[y.index(min(y))], min(y) - 5), 
                arrowprops=dict(facecolor='black', arrowstyle='->')
            )

    plt.title('Time-Weighted Return vs Market')

    # Format x-axis as dates
    # plt.xlabel('Date')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    # plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=20))  # adjust interval as needed
    plt.gcf().autofmt_xdate()

    # Format y-axis as dollars
    plt.ylabel('Value of $100')
    formatter = ticker.FuncFormatter(lambda x, pos: '${:,.0f}'.format(x))
    plt.gca().yaxis.set_major_formatter(formatter)
    plt.legend(loc='upper left')
    # plt.yscale('log')
    plt.tight_layout()
    plt.show()

    # with open('Random/Sofi/data/vs_market_output.csv', 'w', newline='') as f:
    #     dict_writer = csv.DictWriter(f, ['timestamp', 'value', 'change', 'TWR'] + list(market_data.keys()) , extrasaction='ignore')
    #     dict_writer.writeheader()
    #     dict_writer.writerows(data)

    return

if __name__ == "__main__":
    cfg = configparser.ConfigParser()
    cfg.read('Random/Sofi/data/default.cfg')
    apikey = cfg.get('KEYS', 'api_key', raw='')
    output_size = cfg.get('SETTINGS', 'output_size', raw='')
    symbols = cfg.get('SETTINGS', 'symbols', raw='').split(',')
    use_cached_response = cfg.get('SETTINGS', 'use_cached_response', raw='').lower() == 'true'
    dir_data = cfg.get('ENVIRONMENT', 'dir_data', raw='')

    exit(
        main(symbols, apikey, output_size, use_cached_response, dir_data)
    )
    
