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

db_filename = 'test.db'

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

    exchange_rate = 0.0
    KRW2USD_limit = -4.5 #역프 때 이득 
    KRW2USD_offset = 1.5   
    KRW2USD_weighted = KRW2USD_limit + KRW2USD_offset

    USD2KRW_limit = 5.0 #김프 때 이득
    USD2KRW_offset = -1.0
    USD2KRW_weighted = USD2KRW_limit + USD2KRW_offset
    
    weight_offset = 0.0

    KRW2USD = 0.0
    USD2KRW = 0.0

    krw_ask = 0.0
    krw_bid = 0.0
    krw_ask_qty = 0.0
    krw_bid_qty = 0.0
    usd_ask = 0.0
    usd_bid = 0.0
    usd_ask_qty = 0.0
    usd_bid_qty = 0.0
    krw_limit = 50000
    usd_limit = 0.0
    
    krw_timestamp = 0.0
    usd_timestamp = 0.0

    cross_order_unit = 0.001
    btc_stop_unit = 0.005

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

    def cooldown_order(self):
        self.order_flag = False
        t = threading.Thread(target=self.worker_cooldown)
        t.start()

    def worker_logger(self):
        db = sqlite3.connect(db_filename, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS coin_premium(date timestamp, KRW2USD FLOAT, USD2KRW FLOAT, KRW_ASK FLOAT, KRW_BID FLOAT, USD_ASK FLOAT, USD_BID FLOAT, EXCHANGE_RATE FLOAT)''')
        db.commit()
        while True:        
            text = '%.3f, %.3f, %d, %d, %f, %f, %.2f' % (self.KRW2USD, self.USD2KRW, self.krw_ask, self.krw_bid, self.usd_ask, self.usd_bid, self.exchange_rate)
            logging.info(text)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
            cursor.execute('''INSERT INTO coin_premium(date, KRW2USD, USD2KRW, KRW_ASK, KRW_BID, USD_ASK, USD_BID, EXCHANGE_RATE) VALUES(?,?,?,?,?,?,?,?)''', (now,self.KRW2USD, self.USD2KRW, self.krw_ask, self.krw_bid, self.usd_ask, self.usd_bid, self.exchange_rate))
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
        
    def loop(self, upbitws):
        while True:
            if upbitws.codeindex:             
                if self.exchange_rate:
                    self.usd_limit = self.krw_limit / self.exchange_rate
                                   
                update_flag = False                
                upbitws.lock_a.acquire()
                
                #get data from upbit websocket
                if upbitws.data_flag and upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units and upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units:
                    self.krw_timestamp = upbitws.orderbook[upbitws.codeindex['KRW-BTC']].timestamp
                    self.usd_timestamp = upbitws.orderbook[upbitws.codeindex['USDT-BTC']].timestamp
                    for i in range(10):
                        self.krw_ask = upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].ask_price
                        self.krw_ask_qty += upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].ask_size
                        if self.krw_ask_qty * self.krw_ask > self.krw_limit:
                            break
                    for i in range(10):
                        self.krw_bid = upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].bid_price
                        self.krw_bid_qty += upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].bid_size
                        if self.krw_bid_qty * self.krw_bid > self.krw_limit:
                            break
                    for i in range(10):
                        self.usd_ask = upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].ask_price
                        self.usd_ask_qty += upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].ask_size
                        if self.usd_ask_qty * self.usd_ask > self.usd_limit:
                            break
                    for i in range(10):
                        self.usd_bid = upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].bid_price
                        self.usd_bid_qty += upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].bid_size
                        if self.usd_bid_qty * self.usd_bid > self.usd_limit:
                            break              
                        upbitws.data_flag = False
                    update_flag = True                
                
                upbitws.lock_a.release()
                
                #timestamp 차이 10초 미만, 김프 계산식에 사용할 변수들 0이 아닌 경우 진행
                if update_flag:
                    if time.time() - self.krw_timestamp - self.usd_timestamp < 10 and self.usd_bid > 0.0 and self.usd_ask > 0.0 and self.krw_ask > 0.0 and self.krw_bid > 0.0 and self.exchange_rate > 0.0:
                        self.KRW2USD = (self.krw_ask - self.usd_bid * self.exchange_rate)/(self.usd_bid * self.exchange_rate) * 100
                        self.USD2KRW = (self.krw_bid - self.usd_ask * self.exchange_rate)/(self.usd_ask * self.exchange_rate) * 100
                        
                        
                        if self.balance['BTC'] > self.cross_order_unit and self.order_flag and self.balance['BTC'] < self.btc_stop_unit:
                            if self.KRW2USD < self.KRW2USD_weighted and self.balance['KRW'] > self.cross_order_unit*self.krw_ask*1.1 : 
                                #역프 설정된 값보다 작은 경우, 실행
                                #KRW2USD, KRW-BTC:매수;bid , USDT-BTC:매도;ask
                                t1 = threading.Thread(target=self.order,args=('KRW-BTC','bid', self.market_price(self.krw_ask, 1.1), self.cross_order_unit))
                                t2 = threading.Thread(target=self.order,args=('USDT-BTC','ask', self.market_price(self.usd_bid, 0.9), self.cross_order_unit))
                                t1.start()
                                t2.start()
                                t1.join()
                                t2.join()
                                self.cooldown_order()
                                logging.info('KRW2USD!!')                               
                                    
                            elif self.USD2KRW > self.USD2KRW_weighted and self.balance['USDT'] > self.cross_order_unit*self.usd_ask*1.1 : 
                                #김프 설정된 값보다 큰 경우, 실행
                                #USD2KRW, KRW-BTC:매도 , USDT-BTC:매수
                                t1 = threading.Thread(target=self.order,args=('KRW-BTC','ask', self.market_price(self.krw_bid, 0.9), self.cross_order_unit))
                                t2 = threading.Thread(target=self.order,args=('USDT-BTC','bid', self.market_price(self.usd_ask, 1.1), self.cross_order_unit))
                                t1.start()
                                t2.start()
                                t1.join()
                                t2.join()
                                self.cooldown_order()
                                logging.info('USD2KRW')
                        elif self.balance['BTC'] < self.cross_order_unit and self.order_flag and self.balance['BTC'] < self.btc_stop_unit:
                            #buy cross_order_unit to prepare
                            if self.balance['KRW'] > self.cross_order_unit*self.krw_ask: #원화부터 소모 수수료가 싸니까
                                self.order('KRW-BTC','bid', self.market_price(self.krw_ask, 1.1), self.cross_order_unit)
                                self.cooldown_order()
                                #self.get_accounts()

                            logging.info('Buy a cross order unit of BTC')
                        
                        # Cross-order using thread (twice better than sequential)                        
                        '''
                        t1 = threading.Thread(target=self.get_accounts)
                        t2 = threading.Thread(target=self.get_accounts)
                        t1.start()
                        t2.start()
                        t1.join()
                        t2.join()
                        '''

                        time.sleep(0.1)
                    else:
                        logging.info('Error %d %d %d %f %f %f %f %f'% (time.time() * 2000 - self.krw_timestamp - self.usd_timestamp, self.krw_timestamp,self.usd_timestamp, self.usd_bid, self.usd_ask, self.krw_ask, self.krw_bid, self.exchange_rate))
          

    def get_accounts(self):
        upbit = Upbitpy(self.KEY, self.SECRET)
        ret = upbit.get_accounts()
        for c in ret:
            self.balance[c['currency']] = float(c['balance'])
        
        if (self.balance['KRW'] > 0.0 or self.balance['USDT']  > 0.0) and self.exchange_rate > 0.0:
            #보유자산에 따른 KRW2USD_limit and USD2KRW_limt 가중치 부여            
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
            
        logging.info('Weight %.2f %.2f'%(self.KRW2USD_weighted, self.USD2KRW_weighted))


    def get_chance(self, code):
        upbit = Upbitpy(self.KEY, self.SECRET)
        ret = upbit.get_chance(code)
        logging.info(ret)

 
    def order(self, code, dir, price, qty):
        upbit = Upbitpy(self.KEY, self.SECRET)
        ret = upbit.order(code, dir, qty, price) #e.g. ('KRW-BTC', 'bid', 10, 300)
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
    upbit.set_type("orderbook",["KRW-BTC","USDT-BTC"])
    upbit.run()

if __name__ == '__main__':
    if platform.system() == 'Linux':
        logging.basicConfig(filename='test.log', format='%(asctime)s, %(message)s', level=logging.INFO, datefmt='20%y-%m-%d %H:%M:%S')
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
