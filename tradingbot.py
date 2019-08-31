from upbitpy import Upbitpy
import mykey
import logging
import threading
import upbitwspy
import time
import requests #for real currency rate
import json #for real currency rate
import logging
import platform
import sqlite3
import datetime

db_filename = 'mybot.db'

class Orderbook(object):
    def __init__(self, code):
        self.code = ''        
        self.timestamp = 0
        self.ask = 0.0
        self.bid = 0.0

class Tradingbot():
    KEY = ''
    SECRET = ''

    TEST_MARKET = ''
    TEST_BID_PRICE = 0
    TEST_VOLUME = 0
    balance = {}
    balance['KRW'] = 0.0
    balance['USDT'] = 0.0
    balance['BTC'] = 0.0
    balance['ETH'] = 0.0
    balance['XRP'] = 0.0

    exchange_rate = 0.0
    
    KRW2USD_limit = -3.0 #역프 때 이득 
    KRW2USD_offset = 1.0
    KRW2USD_weighted = KRW2USD_limit + KRW2USD_offset

    USD2KRW_limit = 3.0 #김프 때 이득
    USD2KRW_offset = -1.0
    USD2KRW_weighted = USD2KRW_limit + USD2KRW_offset
    USD2KRW_restrict = 1.0

    weight_offset = 0.0

    # KRW2USD = 0.0
    # USD2KRW = 0.0
    # KRW2USD_ETH = 0.0
    # USD2KRW_ETH = 0.0
    # KRW2USD_XRP = 0.0
    # USD2KRW_XRP = 0.0
    KRW2USD = {}    
    KRW2USD['BTC'] = 0.0    
    KRW2USD['ETH'] = 0.0    
    KRW2USD['XRP'] = 0.0

    USD2KRW = {}
    USD2KRW['BTC'] = 0.0
    USD2KRW['ETH'] = 0.0
    USD2KRW['XRP'] = 0.0

    mybook = {}
    mybook['KRW-BTC'] = Orderbook('KRW-BTC')
    mybook['KRW-ETH'] = Orderbook('KRW-ETH')
    mybook['KRW-XRP'] = Orderbook('KRW-XRP')
    mybook['USDT-BTC'] = Orderbook('USDT-BTC')
    mybook['USDT-ETH'] = Orderbook('USDT-ETH')
    mybook['USDT-XRP'] = Orderbook('USDT-XRP')

    krw_ask = 0.0
    krw_bid = 0.0
    krw_ask_qty = 0.0
    krw_bid_qty = 0.0
    usd_ask = 0.0
    usd_bid = 0.0
    usd_ask_qty = 0.0
    usd_bid_qty = 0.0
    krw_limit = 60000
    usd_limit = 0.0
    
    krw_timestamp = 0.0
    usd_timestamp = 0.0

    cross_order_unit = {}
    cross_order_unit['BTC'] = 0.005
    cross_order_unit['ETH'] = 0.2
    cross_order_unit['XRP'] = 150
    stop_order_unit = {}
    stop_order_unit['BTC'] = 0.01
    stop_order_unit['ETH'] = 0.5
    stop_order_unit['XRP'] = 200

    order_flag = False

    def __init__(self, key, secret):
        self.KEY = key
        self.SECRET = secret

        
    def worker_get_info(self):
        while True:
            if self.exchange_rate == 0.0:
                time.sleep(10)
            else:
                time.sleep(60)
            #TODO : Lock before get information
            self.get_real_currency()
            self.get_accounts()
            
    def worker_cooldown(self):        
        if self.order_flag == False:
            time.sleep(5)
            self.get_accounts()
            self.order_flag = True
        time.sleep(1)

    def KRW2USD_exec(self, coin):
        now = time.time()
        if now - self.mybook['KRW-'+coin].timestamp - self.mybook['USDT-'+coin].timestamp < 10:
            if self.KRW2USD[coin] < self.KRW2USD_weighted and self.balance['KRW'] > self.cross_order_unit[coin]*self.mybook['KRW-'+coin].ask * 1.1 and self.balance[coin] < self.stop_order_unit[coin] and self.balance[coin] > self.cross_order_unit[coin] : 
                #역프 설정된 값보다 작은 경우, 실행
                #KRW2USD, KRW-BTC:매수;bid , USDT-BTC:매도;ask
                t1 = threading.Thread(target=self.order,args=('KRW-'+coin,'bid', self.market_price(self.mybook['KRW-'+coin].ask , 1.1), self.cross_order_unit[coin]))
                t2 = threading.Thread(target=self.order,args=('USDT-'+coin,'ask', self.market_price(self.mybook['USDT-'+coin].bid, 0.9), self.cross_order_unit[coin]))
                t1.start()
                t2.start()
                t1.join()
                t2.join()
                self.cooldown_order()
                logging.info('KRW2USD_' + coin)
                time.sleep(0.1)

    def USD2KRW_exec(self, coin):
        now = time.time()
        if now - self.mybook['KRW-'+coin].timestamp - self.mybook['USDT-'+coin].timestamp < 10:
            if self.USD2KRW[coin] > self.USD2KRW_weighted and self.balance['USDT'] > self.cross_order_unit[coin]*self.mybook['USDT-'+coin].ask * 1.1 and self.balance[coin] < self.stop_order_unit[coin] and self.balance[coin] > self.cross_order_unit[coin]: 
                #김프 설정된 값보다 큰 경우, 실행
                #USD2KRW, KRW-BTC:매도 , USDT-BTC:매수            
                t1 = threading.Thread(target=self.order,args=('KRW-'+coin,'ask', self.market_price(self.mybook['KRW-'+coin].bid, 0.9), self.cross_order_unit[coin]))
                t2 = threading.Thread(target=self.order,args=('USDT-'+coin,'bid', self.market_price(self.mybook['USDT-'+coin].ask, 1.1), self.cross_order_unit[coin]))
                t1.start()
                t2.start()
                t1.join()
                t2.join()
                self.cooldown_order()
                logging.info('USD2KRW_'+coin)
                time.sleep(0.1)

    def cooldown_order(self):
        self.order_flag = False
        t = threading.Thread(target=self.worker_cooldown)
        t.start()

    def worker_logger(self):
        db = sqlite3.connect(db_filename, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS upbit_premium(date timestamp, 
            KRW2USD FLOAT, USD2KRW FLOAT, KRW2USD_ETH FLOAT, USD2KRW_ETH FLOAT,
            EXCHANGE_RATE FLOAT, KRW2USD_weight FLOAT, USD2KRW_weight FLOAT)''')
        
        db_patch = []
        db_patch.append("ALTER TABLE upbit_premium ADD column KRW2USD_XRP FLOAT")
        db_patch.append("ALTER TABLE upbit_premium ADD column USD2KRW_XRP FLOAT")
        # db_patch.append("ALTER TABLE coin_premium ADD column balance_krw FLOAT")
        # db_patch.append("ALTER TABLE coin_premium ADD column balance_usd FLOAT")
        for q in db_patch:
            try:
                cursor.execute(q)
            except:
                print('Failed to add a column')
        db.commit()

        while True:       
            #text = '%.3f, %.3f, %d, %d, %f, %f, %.2f' % (self.KRW2USD, self.USD2KRW, self.mybook['KRW-BTC'].ask, self.mybook['KRW-BTC'].bid, self.mybook['USDT-BTC'].ask, self.mybook['USDT-BTC'].bid, self.exchange_rate)
            text = '%.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.2f' % (self.KRW2USD['BTC'], self.USD2KRW['BTC'], self.KRW2USD['ETH'] ,self.USD2KRW['ETH'], self.KRW2USD['XRP'],self.USD2KRW['XRP'], self.exchange_rate)
            logging.info(text)
            if self.mybook['KRW-BTC'].ask > 0.0 and self.mybook['USDT-BTC'].ask > 0.0 and self.exchange_rate > 0.0:                 
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")            
                cursor.execute('''INSERT INTO 
                    upbit_premium(date, KRW2USD, USD2KRW, KRW2USD_ETH, USD2KRW_ETH, KRW2USD_XRP, USD2KRW_XRP,
                    EXCHANGE_RATE, KRW2USD_weight, USD2KRW_weight) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                    (now,self.KRW2USD['BTC'], self.USD2KRW['BTC'], self.KRW2USD['ETH'], self.USD2KRW['ETH'], self.KRW2USD['XRP'], self.USD2KRW['XRP'],
                    self.exchange_rate,self.KRW2USD_weighted, self.USD2KRW_weighted))
                db.commit()
            time.sleep(1)
            
            #time.sleep(1)
    
    def get_real_currency(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        url = 'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD'
        try:
            ret =requests.get(url, headers=headers).json()
        except:
            self.exchange_rate = 0
        #TODO : tracking date "date":"2019-08-09","time":"20:01:00"
        self.exchange_rate = ret[0]['basePrice']
        logging.info('exchange rate was updated %.2f'%tb.exchange_rate)
    
    def rate_limit(self):
        rate = 100* (self.balance['KRW'])/(self.balance['KRW']+self.balance['USDT']*self.exchange_rate)
        if rate > 95:
            return 3.0, 4.0
        elif rate > 90:
            return 2.0, 4.0
        elif rate > 85:
            return 2.0, 3.0
        elif rate > 80:
            return 1.0, 3.0
        elif rate > 70:
            return 1.0, 2.0
        elif rate > 60:
            return 0.0, 2.0
        elif rate > 50:
            return 0.0, 1.2
        elif rate > 45:
            return 0.0, 1.0
        elif rate > 30:
            return -1.0, 1.0
        elif rate > 20:
            return -1.0, 0.0
        elif rate > 15:
            return -2.0, 0.0
        elif rate > 10:
            return -2.0, -1.0
        elif rate > 5:
            return -3.0, -1.0
        else:
            return -3.0, -2.0

    def loop(self, upbitws):
        while True:
            if upbitws.codeindex:             
                if self.exchange_rate:
                    self.usd_limit = self.krw_limit / self.exchange_rate
                                   
                update_flag = False                
                upbitws.lock_a.acquire()
                
                #get data from upbit websocket
                if upbitws.data_flag and upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units and upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units and upbitws.orderbook[upbitws.codeindex['KRW-ETH']].units and upbitws.orderbook[upbitws.codeindex['USDT-ETH']].units and upbitws.orderbook[upbitws.codeindex['KRW-XRP']].units and upbitws.orderbook[upbitws.codeindex['USDT-XRP']].units:
                    self.mybook['KRW-BTC'].timestamp = upbitws.orderbook[upbitws.codeindex['KRW-BTC']].timestamp
                    self.mybook['USDT-BTC'].timestamp = upbitws.orderbook[upbitws.codeindex['USDT-BTC']].timestamp
                    self.mybook['KRW-ETH'].timestamp = upbitws.orderbook[upbitws.codeindex['KRW-ETH']].timestamp
                    self.mybook['USDT-ETH'].timestamp = upbitws.orderbook[upbitws.codeindex['USDT-ETH']].timestamp
                    self.mybook['KRW-XRP'].timestamp = upbitws.orderbook[upbitws.codeindex['KRW-XRP']].timestamp
                    self.mybook['USDT-XRP'].timestamp = upbitws.orderbook[upbitws.codeindex['USDT-XRP']].timestamp
                    
                    #btc
                    qty = 0.0
                    for i in range(10):
                        self.mybook['KRW-BTC'].ask = upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].ask_price
                        qty += upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].ask_size
                        if qty > self.cross_order_unit['BTC'] * 2:
                            break
                    qty = 0.0
                    for i in range(10):
                        self.mybook['KRW-BTC'].bid = upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].bid_price
                        qty += upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].bid_size
                        if qty > self.cross_order_unit['BTC'] * 2:
                            break
                    qty = 0.0
                    for i in range(10):
                        self.mybook['USDT-BTC'].ask = upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].ask_price
                        qty += upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].ask_size
                        if qty > self.cross_order_unit['BTC'] * 2:
                            break
                    qty = 0.0
                    for i in range(10):
                        self.mybook['USDT-BTC'].bid = upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].bid_price
                        qty += upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].bid_size
                        if qty > self.cross_order_unit['BTC'] * 2:
                            break              
                    #eth
                    qty = 0.0
                    for i in range(10):
                        self.mybook['KRW-ETH'].ask = upbitws.orderbook[upbitws.codeindex['KRW-ETH']].units[i].ask_price
                        qty += upbitws.orderbook[upbitws.codeindex['KRW-ETH']].units[i].ask_size
                        if qty > self.cross_order_unit['ETH'] * 2:
                            break
                    qty = 0.0
                    for i in range(10):
                        self.mybook['KRW-ETH'].bid = upbitws.orderbook[upbitws.codeindex['KRW-ETH']].units[i].bid_price
                        qty += upbitws.orderbook[upbitws.codeindex['KRW-ETH']].units[i].bid_size
                        if qty > self.cross_order_unit['ETH'] * 2:
                            break
                    qty = 0.0
                    for i in range(10):
                        self.mybook['USDT-ETH'].ask = upbitws.orderbook[upbitws.codeindex['USDT-ETH']].units[i].ask_price
                        qty += upbitws.orderbook[upbitws.codeindex['USDT-ETH']].units[i].ask_size
                        if qty > self.cross_order_unit['ETH'] * 2:
                            break
                    qty = 0.0
                    for i in range(10):
                        self.mybook['USDT-ETH'].bid = upbitws.orderbook[upbitws.codeindex['USDT-ETH']].units[i].bid_price
                        qty += upbitws.orderbook[upbitws.codeindex['USDT-ETH']].units[i].bid_size
                        if qty > self.cross_order_unit['ETH'] * 2:
                            break              

                    #xrp
                    qty = 0.0
                    for i in range(10):
                        self.mybook['KRW-XRP'].ask = upbitws.orderbook[upbitws.codeindex['KRW-XRP']].units[i].ask_price
                        qty += upbitws.orderbook[upbitws.codeindex['KRW-XRP']].units[i].ask_size
                        if qty > self.cross_order_unit['XRP'] * 2:
                            break
                    qty = 0.0
                    for i in range(10):
                        self.mybook['KRW-XRP'].bid = upbitws.orderbook[upbitws.codeindex['KRW-XRP']].units[i].bid_price
                        qty += upbitws.orderbook[upbitws.codeindex['KRW-XRP']].units[i].bid_size
                        if qty > self.cross_order_unit['XRP'] * 2:
                            break
                    qty = 0.0
                    for i in range(10):
                        self.mybook['USDT-XRP'].ask = upbitws.orderbook[upbitws.codeindex['USDT-XRP']].units[i].ask_price
                        qty += upbitws.orderbook[upbitws.codeindex['USDT-XRP']].units[i].ask_size
                        if qty > self.cross_order_unit['XRP'] * 2:
                            break
                    qty = 0.0
                    for i in range(10):
                        self.mybook['USDT-XRP'].bid = upbitws.orderbook[upbitws.codeindex['USDT-XRP']].units[i].bid_price
                        qty += upbitws.orderbook[upbitws.codeindex['USDT-XRP']].units[i].bid_size
                        if qty > self.cross_order_unit['XRP'] * 2:
                            break    

                    upbitws.data_flag = False
                    update_flag = True                
                
                upbitws.lock_a.release()
                
                #timestamp 차이 10초 미만, 김프 계산식에 사용할 변수들 0이 아닌 경우 진행
                if update_flag:
                    now = time.time()
                    if now - self.mybook['KRW-BTC'].timestamp - self.mybook['USDT-BTC'].timestamp < 10 and self.mybook['USDT-BTC'].bid > 0.0 and self.mybook['KRW-BTC'].ask > 0.0 and self.exchange_rate > 0.0:
                        self.KRW2USD['BTC'] = (self.mybook['KRW-BTC'].ask  - self.mybook['USDT-BTC'].bid * self.exchange_rate)/(self.mybook['USDT-BTC'].bid * self.exchange_rate) * 100
                        self.USD2KRW['BTC'] = (self.mybook['KRW-BTC'].bid - self.mybook['USDT-BTC'].ask * self.exchange_rate)/(self.mybook['USDT-BTC'].ask * self.exchange_rate) * 100
                    if now - self.mybook['KRW-ETH'].timestamp - self.mybook['USDT-ETH'].timestamp < 10 and self.mybook['USDT-ETH'].bid > 0.0 and self.mybook['KRW-BTC'].ask > 0.0 and self.exchange_rate > 0.0:
                        self.KRW2USD['ETH'] = (self.mybook['KRW-ETH'].ask  - self.mybook['USDT-ETH'].bid * self.exchange_rate)/(self.mybook['USDT-ETH'].bid * self.exchange_rate) * 100
                        self.USD2KRW['ETH'] = (self.mybook['KRW-ETH'].bid - self.mybook['USDT-ETH'].ask * self.exchange_rate)/(self.mybook['USDT-ETH'].ask * self.exchange_rate) * 100 
                    if now - self.mybook['KRW-XRP'].timestamp - self.mybook['USDT-XRP'].timestamp < 10 and self.mybook['USDT-XRP'].bid > 0.0 and self.mybook['KRW-XRP'].ask > 0.0 and self.exchange_rate > 0.0:                      
                        self.KRW2USD['XRP'] = (self.mybook['KRW-XRP'].ask  - self.mybook['USDT-XRP'].bid * self.exchange_rate)/(self.mybook['USDT-XRP'].bid * self.exchange_rate) * 100
                        self.USD2KRW['XRP'] = (self.mybook['KRW-XRP'].bid - self.mybook['USDT-XRP'].ask * self.exchange_rate)/(self.mybook['USDT-XRP'].ask * self.exchange_rate) * 100       

                    
                    # timestamp max dictionary index
                    if self.order_flag :
                        #Find Min 역프는 작을수록 유리
                        code = 'BTC'
                        if self.KRW2USD['BTC'] > self.KRW2USD['ETH']:
                            code = 'ETH'
                        if self.KRW2USD[code] > self.KRW2USD['XRP']:
                            code = 'XRP'
                    
                        self.KRW2USD_exec(code)                                
                        
                        #Find Max 역프는 작을수록 유리
                        code = 'BTC'
                        if self.USD2KRW['BTC'] < self.USD2KRW['ETH']:
                            code = 'ETH'
                        if self.USD2KRW[code] < self.USD2KRW['XRP']:
                            code = 'XRP'                            
                        
                        self.USD2KRW_exec(code)
                        
                        #TODO : buy if cross_order_unit is smaller than settings
                        # elif self.balance['BTC'] < self.cross_order_unit and self.order_flag and self.balance['BTC'] < self.btc_stop_unit:
                        #     #buy cross_order_unit to prepare
                        #     if self.balance['KRW'] > self.cross_order_unit*self.mybook['KRW-BTC'].ask*1.1: #원화부터 소모 수수료가 싸니까
                        #         self.order('KRW-BTC','bid', self.market_price(self.mybook['KRW-BTC'].ask, 1.1), self.cross_order_unit)
                        #         self.cooldown_order()
                        #         #self.get_accounts()
                        #     elif self.balance['USDT'] > self.cross_order_unit*self.mybook['USDT-BTC'].ask*1.1:
                        #         self.order('USDT-BTC','bid', self.market_price(self.mybook['USDT-BTC'].ask, 1.1), self.cross_order_unit)
                        #         self.cooldown_order()

                        #     logging.info('Buy a cross order unit of BTC')
                        
                        time.sleep(0.1)
                    # else:
                    #     logging.info('Error %d %d %d %f %f %f %f %f'% (time.time() * 2000 - self.mybook['KRW-BTC'].timestamp - self.mybook['USDT-BTC'].timestamp, self.mybook['KRW-BTC'].timestamp,self.mybook['USDT-BTC'].timestamp, self.mybook['USDT-BTC'].bid, self.mybook['USDT-BTC'].ask, self.mybook['KRW-BTC'].ask, self.mybook['KRW-BTC'].bid, self.exchange_rate))
            time.sleep(0.001)
          

    def get_accounts(self):
        try:
            upbit = Upbitpy(self.KEY, self.SECRET)
            ret = upbit.get_accounts()
            for c in ret:
                self.balance[c['currency']] = float(c['balance'])
        except:
            self.balance['KRW'] = 0
            self.balance['USDT'] = 0
            logging.info('Failed to get balance')

        if (self.balance['KRW'] > 0.0 or self.balance['USDT']  > 0.0) and self.exchange_rate > 0.0:
            # 보유자산에 따른 KRW2USD_limit and USD2KRW_limt 가중치 부여 점진법
            self.KRW2USD_weighted = self.KRW2USD_limit - self.KRW2USD_limit*self.balance['KRW']/(self.balance['KRW'] + self.balance['USDT']*self.exchange_rate)           
            self.USD2KRW_weighted = self.USD2KRW_limit - self.USD2KRW_limit*self.balance['USDT']*self.exchange_rate/(self.balance['KRW'] + self.balance['USDT']*self.exchange_rate)
            if self.KRW2USD_weighted >= self.KRW2USD_limit and self.KRW2USD_weighted <= self.USD2KRW_limit:
                self.KRW2USD_weighted = self.KRW2USD_weighted + self.KRW2USD_offset
            else:
                self.KRW2USD_weighted = self.KRW2USD_limit                
            if self.USD2KRW_weighted >= self.KRW2USD_limit and self.USD2KRW_weighted <= self.USD2KRW_limit:
                self.USD2KRW_weighted = self.USD2KRW_weighted + self.USD2KRW_offset
            else:
                self.USD2KRW_weighted = self.USD2KRW_limit

            if self.USD2KRW_weighted < self.USD2KRW_restrict:
                self.USD2KRW_weighted = self.USD2KRW_weighted / 4 + 0.75
                # self.USD2KRW_weighted = self.USD2KRW_restrict
            if self.KRW2USD_weighted > 0.0:
                self.KRW2USD_weighted = self.KRW2USD_weighted * 0.5
            #보유자산에 따른 KRW2USD_limit and USD2KRW_limt 가중치 부여 계단법
            #temp, self.USD2KRW_weighted = self.rate_limit()

        logging.info('Weight %.2f %.2f'%(self.KRW2USD_weighted, self.USD2KRW_weighted))


    def get_chance(self, code):
        upbit = Upbitpy(self.KEY, self.SECRET)
        ret = upbit.get_chance(code)
        logging.info(ret)

 
    def order(self, code, dir, price, qty):
        upbit = Upbitpy(self.KEY, self.SECRET)
        ret = upbit.order(code, dir, qty, price) #e.g. ('KRW-BTC', 'bid', 10, 300)
        logging.info('%s, %s, %d, %.2f'%(code,dir,price,qty))
        logging.info(ret)
        
    def market_price(self, number, weight):      #only if price is greater than 100
        count = self.digit_count(number)
        number = number * weight
        
        for t in range(count - 3):
            number = number /10
        number = int(number)
        for t in range(count - 3):
            number = number * 10
        return number

    def digit_count(self, number):
        count = 0
        while(number > 0):
            number = number // 10
            count = count + 1
        return count

    def test_get_orders(self):
        upbit = Upbitpy(self.KEY, self.SECRET)
        self.__do_temp_order(upbit)
        ret = upbit.get_orders(self.TEST_MARKET, 'wait')
        logging.info(ret)
        self.__do_cancel(upbit)


    def test_cancel_order(self):
        upbit = Upbitpy(self.KEY, self.SECRET)
        uuid = self.__do_temp_order(upbit)
        ret = upbit.cancel_order(uuid)
        logging.info(ret)


    def __do_cancel(self, upbit):
        uuid = self.__get_temp_order(upbit)
        if uuid is not None:
            upbit.cancel_order(uuid)


    def __do_temp_order(self, upbit):
        upbit.order(self.TEST_MARKET, 'bid', self.TEST_VOLUME, self.TEST_BID_PRICE)
        ret = upbit.get_orders(self.TEST_MARKET, 'wait')
        if ret is None or len(ret) == 0:
            return None
        return ret[0]['uuid']


    def __get_temp_order(self, upbit):
        ret = upbit.get_orders(self.TEST_MARKET, 'wait')
        if ret is None or len(ret) == 0:
            return None
        return ret[0]['uuid']

#For thread

def worker_get_orderbook(upbit):
    #start worker
    upbit.set_type("orderbook",["KRW-BTC","USDT-BTC","KRW-ETH","USDT-ETH","KRW-XRP","USDT-XRP"])
    upbit.run()

if __name__ == '__main__':
    if platform.system() == 'Linux':
        logging.basicConfig(filename='mybot.log', format='%(asctime)s, %(message)s', level=logging.INFO, datefmt='20%y-%m-%d %H:%M:%S')
    else:       # equal 'Windows'
        logging.basicConfig(format='%(asctime)s, %(message)s', level=logging.INFO, datefmt='20%y-%m-%d %H:%M:%S')
    
    
    tb = Tradingbot(mykey.ACCESS_KEY, mykey.SECRET_KEY)    
    #get exchange rate and then get accounts!!! for weight
    tb.get_real_currency()
    tb.get_accounts()
    

    upbitws = upbitwspy.UpbitWebsocket()

    t1 = threading.Thread(target=worker_get_orderbook, args=(upbitws,))
    t1.start()

    t2 = threading.Thread(target=tb.worker_get_info)
    t2.start()

    t3 = threading.Thread(target=tb.worker_logger)
    t3.start()

    main_thread = threading.currentThread()

    tb.order_flag = True
    tb.loop(upbitws)

    for t in threading.enumerate():
        if t is not main_thread:
            t.join()
    #tb.get_chance('KRW-BTC')
    #tb.order('USDT-BTC','bid', 11500, 0.0003) #매수
    #tb.order('KRW-BTC','ask', 13000000, 0.0005) #매도
    #tb.order('KRW-BTC','bid', 14000000, 0.0005) #매수
   # tb.get_chance('KRW-BTC')
