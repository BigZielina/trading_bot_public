import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from pandas import DataFrame
from statsmodels.tsa.arima_model import ARMA
import statsmodels.tsa.arima_model
import pandas_ta as ta
from binance.client import Client
from statsmodels.tsa.arima_model import ARIMA, ARMA
from time import time
from statsmodels.tsa.vector_ar import util
from statsmodels.tsa.ar_model import AR
import statsmodels.api as sm
from binance.client import Client
import time
import pandas as pd
from string import ascii_uppercase
from binance.client import Client
from binance.enums import *
from datetime import datetime
import pytz
import csv

def get_api(): 
    key=""
    secret = ""

    return key, secret


api_key, api_secret = get_api()
client = Client(api_key, api_secret)
print("START")

def getdata(symbol,interval,period):
    frame = pd.DataFrame(client.futures_historical_klines(symbol,interval,period))

    frame = frame.iloc[:,0:6]
    frame.columns = ['Time','Open','High','Low','Close','Volume']
    frame.set_index('Time', inplace = True)
    frame.index = pd.to_datetime(frame.index,unit='ms')
    frame = frame.astype(float)
    return frame

def arima_predict(symbol, interval):
    df = getdata(symbol,interval,'365 days ago UTC')
    market = df['Close']
    returns = market.dropna().tolist()
    returns.pop()
    model = sm.tsa.arima.ARIMA(returns, order=(2,1,2))
    result = model.fit()
    pred = (result.forecast(steps=1, exog=1, alpha=0.05))
    return pred[0]

def arima_predict2(symbol, interval):
    df = getdata(symbol,interval,'365 days ago UTC')
    market = df['Close']
    returns = market.dropna().tolist()
    model = sm.tsa.arima.ARIMA(returns, order=(2,1,2))
    result = model.fit()
    pred = (result.forecast(steps=1, exog=1, alpha=0.05))
    return pred[0]

def stoch_change(symbol, interval):
    df = getdata(symbol,interval,"12 hours ago UTC")
    df.ta.stoch(high='high', low='low', k=5, d=3, append=True)
    k_past = df['STOCHk_5_3_3'].tolist()[-3]
    d_past = df['STOCHd_5_3_3'].tolist()[-3]
    k_current = df['STOCHk_5_3_3'].tolist()[-2]
    d_current = df['STOCHd_5_3_3'].tolist()[-2]
    # print("K_past:",k_past," D_past", d_past)
    print("K: ",k_current," D: ", d_current)


    a1 = d_current - d_past
    b1 = d_past - a1
    a2 = k_current - k_past
    b2 = k_past - a2
    x = (b2 - b1)/(a1 - a2)
    value = a1 * x + b1
    # print(value)

    if k_past>d_past and k_current<d_current and (value> 80):     #idzie w dol
        return -1                                
    elif k_past<d_past and k_current>d_current and (value< 20):     #idzie w gore
        return 1
    else:
        return 0        #nic sie nie zmienia

def check_candle_long(symbol, interval):
    df = getdata(symbol,interval,"5 days ago UTC")
    candle1 = df['Close'].tolist()[-2] - df['Open'].tolist()[-2]
    if abs(candle1/df['Open'].tolist()[-2]) < 0.0001:
        return 1
    elif candle1 > 0: #add candle
        return 1
    elif candle1 < 0: # sell
        return -1

def check_candle_short(symbol, interval):
    df = getdata(symbol,interval,"5 days ago UTC")
    candle1 = df['Close'].tolist()[-2] - df['Open'].tolist()[-2]
    if abs(candle1/df['Open'].tolist()[-2]) < 0.0001:
        return -1
    elif candle1 > 0: #sell
        return 1
    elif candle1 < 0: # add candle
        return -1


def synchronize(symbol, interval_no):
    while True:
        tz_NY = pytz.timezone('America/New_York') 
        datetime_NY = datetime.now(tz_NY)
        minute = int(datetime_NY.strftime("%M"))
        hour = int(datetime_NY.strftime("%H"))
        # print(interval_no,hour, minute, datetime_NY)
        # time.sleep(5.0)                                     # 5 sec!!!
        # if interval_no == 0 and minute%5 == 0:
        #     print("sync")
        #     break
        if interval_no == 0 and minute%15 == 0:
            print("synchronized 15m")
            break
        elif interval_no == 1 and minute == 0:
            print("synchronized 1h")
            break
        elif interval_no == 2 and hour%4==0 and minute ==0:
            print("synchronized 4h")
            break
        elif interval_no == 3 and hour%12==0 and minute ==0:
            print("synchronized 12h")
            break
            
        time.sleep(1.0)

def get_balance_futures():
    info = client.get_account_snapshot(type='FUTURES')
    snapshot = info['snapshotVos'][0]
    assets = snapshot['data']
    for i in range(len(assets['assets'])):
        if assets['assets'][i]['asset'] == 'USDT':
            return float((assets['assets'][0]['marginBalance']))

def open_long_k():
    price_f = client.futures_symbol_ticker(symbol='BTCUSDT')
    price_f = float(price_f["price"])
    price_f = round(price_f,4)
    usdt = 50

    client.futures_change_leverage(symbol='BTCUSDT', leverage=1)

    q = round(usdt/price_f,3)

    client.futures_create_order(
        symbol='BTCUSDT',
        type='MARKET',
        side='BUY',
        quantity=q,
    )

    client.futures_create_order(
        symbol='BTCUSDT',
        type='STOP_MARKET',
        side='SELL',
        quantity=q,
        stopPrice=round(0.9875*price_f,2),
        closePosition=True
    )
    return q


def open_short_k():
    price_f = client.futures_symbol_ticker(symbol='BTCUSDT')
    price_f = float(price_f["price"])
    price_f = round(price_f,4)
    usdt = 50

    client.futures_change_leverage(symbol='BTCUSDT', leverage=1)

    q = round(usdt/price_f,3)

    client.futures_create_order(
        symbol='BTCUSDT',
        type='MARKET',
        side='SELL',
        quantity=q,
    )

    client.futures_create_order(
        symbol='BTCUSDT',
        type='STOP_MARKET',
        side='BUY',
        quantity=q,
        stopPrice=round(1.0125*price_f,2),
        closePosition=True
    )
    return q

def open_long():
    price_f = client.futures_symbol_ticker(symbol='BTCUSDT')
    price_f = float(price_f["price"])
    price_f = round(price_f,4)
    usdt = get_balance_futures()

    client.futures_change_leverage(symbol='BTCUSDT', leverage=1)

    q = round(usdt/price_f,3)
    while(q>usdt/price_f):
        q = q*0.995

    client.futures_create_order(
        symbol='BTCUSDT',
        type='MARKET',
        side='BUY',
        quantity=q,
    )

    client.futures_create_order(
        symbol='BTCUSDT',
        type='STOP_MARKET',
        side='SELL',
        quantity=q,
        stopPrice=round(0.9875*price_f,2),
        closePosition=True
    )
    return q


def open_short():
    price_f = client.futures_symbol_ticker(symbol='BTCUSDT')
    price_f = float(price_f["price"])
    price_f = round(price_f,4)
    usdt = get_balance_futures()

    client.futures_change_leverage(symbol='BTCUSDT', leverage=1)

    q = round(usdt/price_f,3)

    q = round(usdt/price_f,3)
    while(q>usdt/price_f):
        q = q*0.995

    client.futures_create_order(
        symbol='BTCUSDT',
        type='MARKET',
        side='SELL',
        quantity=q,
    )

    client.futures_create_order(
        symbol='BTCUSDT',
        type='STOP_MARKET',
        side='BUY',
        quantity=q,
        stopPrice=round(1.0125*price_f,2),
        closePosition=True
    )
    return q

def close_all_positions_long(q):
    client.futures_cancel_all_open_orders(
    symbol = 'BTCUSDT',
    timestamp = 100
    )
    client.futures_create_order(
        symbol='BTCUSDT',
        type='MARKET',
        side='SELL',
        quantity=q,
        reduceOnly='true'
    )

def close_all_positions_short(q):
    client.futures_cancel_all_open_orders(
    symbol = 'BTCUSDT',
    timestamp = 100
    )
    client.futures_create_order(
        symbol='BTCUSDT',
        type='MARKET',
        side='BUY',
        quantity=q,
        reduceOnly='true'
    )

def write_to_csv(price,direction,slot):
    data =[]
    
    tz_NY = pytz.timezone('America/New_York') 
    datetime_NY = datetime.now(tz_NY)
    data.append(datetime_NY)
    
    data.append(price)

    if slot == "hold":
        if direction == "long":
            data.append("Open long")
        elif direction == "short":
            data.append("Open short")
    elif slot == "empty":
        if direction == "long":
            data.append("Close long")
        elif direction == "short":
            data.append("Close short")

    #indicators
    df = getdata(symbol,"5m","1 hour ago UTC")
    df.ta.stoch(high='high', low='low', k=5, d=3, append=True)
    k_current = df['STOCHk_5_3_3'].tolist()[-2]
    d_current = df['STOCHd_5_3_3'].tolist()[-2]
    data.append(k_current)
    data.append(d_current)

    df = getdata(symbol,"15m","20 hours ago UTC")
    df.ta.stoch(high='high', low='low', k=5, d=3, append=True)
    k_current = df['STOCHk_5_3_3'].tolist()[-2]
    d_current = df['STOCHd_5_3_3'].tolist()[-2]
    data.append(k_current)
    data.append(d_current)

    df = getdata(symbol,"1h","20 hours ago UTC")
    df.ta.stoch(high='high', low='low', k=5, d=3, append=True)
    k_current = df['STOCHk_5_3_3'].tolist()[-2]
    d_current = df['STOCHd_5_3_3'].tolist()[-2]
    data.append(k_current)
    data.append(d_current)

    data.append(round(arima_predict(symbol, "1d"),2))
    data.append(round(arima_predict2(symbol, "1d"),2))
    data.append(round(arima_predict(symbol, "12h"),2))
    data.append(round(arima_predict2(symbol, "12h"),2))
    data.append(round(arima_predict(symbol, "8h"),2))
    data.append(round(arima_predict2(symbol, "8h"),2))

    with open('example.csv', 'a') as file:
        writer = csv.writer(file)
        writer.writerow(data)



    
symbol = 'BTCUSDT'
interval = '15m'
candle_counter_long = 0
candle_counter_short = 0
direction = ""  # long / short
q = 0
q1 = 0
q2 = 0
q3 = 0

slot = "empty"
intervals = ['15m', '1h','4h','12h']
interval_no = 0
startime = time.time()


synchronize(symbol, interval_no)

while True:
    if len(client.futures_get_open_orders()) == 0:
        slot="empty"
    time.sleep(3.5)
    price = client.futures_symbol_ticker(symbol='BTCUSDT')
    price = float(price["price"])
    price = round(price,4)
    print(price, round(arima_predict(symbol, "1d"),2), round(arima_predict2(symbol, "1d"),2))


    if slot == "empty":
        interval = intervals[interval_no]

        if stoch_change(symbol, interval) == 1 and arima_predict(symbol, "1d") > price:
            slot = "hold"
            # LONG
            # api_key, api_secret = get_api_3()
            # client = Client(api_key, api_secret)
            # q3 = open_long_k()
            api_key, api_secret = get_api()
            client = Client(api_key, api_secret)
            q2 = open_long()
            api_key, api_secret = get_api()
            client = Client(api_key, api_secret)
            q1 = open_long()
            



            print(price, " buy_long  Arima: ", arima_predict(symbol, "1d"))
            direction = "long"
            write_to_csv(price,direction,slot)


        if stoch_change(symbol, interval) == -1 and arima_predict(symbol, "1d") < price:
            slot = "hold"
            
            #SHORT
            # api_key, api_secret = get_api_3()
            # client = Client(api_key, api_secret)
            # q3 = open_short_k()

            api_key, api_secret = get_api()
            client = Client(api_key, api_secret)
            q2 = open_short()

            api_key, api_secret = get_api()
            client = Client(api_key, api_secret)
            q1 = open_short()
            
            print(price, " buy_short   Arima: ", arima_predict(symbol, "1d"))
            direction = "short"
            write_to_csv(price,direction,slot)

    elif slot == "hold":
        df = getdata(symbol,interval,"4 hours ago UTC")
        df.ta.stoch(high='high', low='low', k=5, d=3, append=True)
        k_current = df['STOCHk_5_3_3'].tolist()[-2]
        print(k_current)
        if direction == "long" and k_current > 79.9:
            slot ="full"
        
        if direction == "short" and k_current < 20.1:
            slot ="full"

    elif slot == "full":
        if direction == "long":
            check_candle = check_candle_long(symbol, interval)

            if check_candle == -1:
        
                #CLOSE LONG
                api_key, api_secret = get_api()
                client = Client(api_key, api_secret)
                close_all_positions_long(q2)

                api_key, api_secret = get_api()
                client = Client(api_key, api_secret)
                close_all_positions_long(q1)

                # api_key, api_secret = get_api_3()
                # client = Client(api_key, api_secret)
                # close_all_positions_long(q3)

                print(price, " sell")
                slot = "empty"
                candle_counter_long = 0
                candle_counter_short = 0
                interval_no = 0 
                write_to_csv(price,direction,slot)

            if check_candle == 1:
                candle_counter_long = candle_counter_long + 1

                if candle_counter_long == 3 and interval_no < 4:
                    candle_counter_long = 0
                    interval_no = interval_no + 1
                    interval = intervals[interval_no]

        elif direction == "short":
            check_candle = check_candle_long(symbol, interval)

            if check_candle_short(symbol, interval) == 1:
                #CLOSE SHORT
                api_key, api_secret = get_api()
                client = Client(api_key, api_secret)
                close_all_positions_short(q2)

                api_key, api_secret = get_api()
                client = Client(api_key, api_secret)
                close_all_positions_short(q1)

                # api_key, api_secret = get_api_3()
                # client = Client(api_key, api_secret)
                # close_all_positions_short(q3)

                print(price, " sell")
                slot = "empty"
                candle_counter_long = 0
                candle_counter_short = 0
                interval_no = 0 
                write_to_csv(price,direction,slot)
            
            if check_candle_short(symbol, interval) == -1:
                candle_counter_short = candle_counter_short + 1
                if candle_counter_short == 4 and interval_no < 4:
                    candle_counter_short = 0
                    interval_no = interval_no + 1
                    interval = intervals[interval_no]

        print("slot is ",slot," price: ",price,"  greens: ", candle_counter_long,"  reds: ", candle_counter_short)
    print(slot)
    print(" ")

    time.sleep(61.0)
    synchronize(symbol, interval_no)