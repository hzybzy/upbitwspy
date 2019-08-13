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
    KRW2USD_limit = -3.0 #역프 때 이득
    USD2KRW_limit = 0.0 #김프 때 이득
    KRW2USD = 0.0
    USD2KRW = 0.0

    def __init__(self, key, secret):
        self.KEY = key
        self.SECRET = secret

    def worker_get_orderbook(self, upbit):
        #start worker
        upbit.set_type("orderbook",["KRW-BTC","USDT-BTC"])
        upbit.run()
    
    
    def worker_exchange_rate(self):
        while True:
            if self.exchange_rate == 0.0:
                time.sleep(10)
            else:
                time.sleep(1000)
            self.get_real_currency()
            logging.info('exchange rate was updated %.2f'%self.exchange_rate)
    
    def worker_logger(self):
        while True:        
            text = 'KRW2USD, USD2KRW, %.3f, %.3f' % (self.KRW2USD, self.USD2KRW)#, krw_timestamp/1000, usd_timestamp/1000, time.time())                
            #text = '%d ask : %f %f bid : %f %f'% (usd_timestamp/1000, usd_ask, usd_ask_qty, usd_bid, usd_bid_qty)
            logging.info(text)
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

    def get_accounts(self):
        upbit = Upbitpy(self.KEY, self.SECRET)
        ret = upbit.get_accounts()
        for c in ret:
            self.balance[c['currency']] = c['balance' ]
        logging.info(self.balance)


    def get_chance(self, code):
        upbit = Upbitpy(self.KEY, self.SECRET)
        ret = upbit.get_chance(code)
        logging.info(ret)


    def order(self, code, dir, price, qty):
        upbit = Upbitpy(self.KEY, self.SECRET)
        ret = upbit.order(code, dir, qty, price) #e.g. ('KRW-XRP', 'bid', 10, 300)
        logging.info(ret)
        


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


if __name__ == '__main__':
    if platform.system() == 'Linux':
        logging.basicConfig(filename='test.log', format='%(asctime)s, %(message)s', level=logging.INFO, datefmt='20%y-%m-%d %H:%M:%S')
    else:       # equal 'Windows'
        logging.basicConfig(format='%(asctime)s, %(message)s', level=logging.INFO, datefmt='20%y-%m-%d %H:%M:%S')
    
    
    tb = Tradingbot(mykey.ACCESS_KEY, mykey.SECRET_KEY)
    tb.get_accounts()
    tb.get_real_currency()

    upbitws = upbitwspy.UpbitWebsocket()

    t1 = threading.Thread(target=tb.worker_get_orderbook, args=(upbitws,))
    t1.start()

    t2 = threading.Thread(target=tb.worker_exchange_rate)
    t2.start()

    t3 = threading.Thread(target=tb.worker_logger)
    t3.start()

    main_thread = threading.currentThread()

    while True:
        if upbitws.codeindex:
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
            if tb.exchange_rate:
                usd_limit = krw_limit / tb.exchange_rate
            
            krw_timestamp = 0.0
            usd_timestamp = 0.0
            
            
            update_flag = False
            upbitws.lock_b.acquire()
            upbitws.lock_a.acquire()
            
            if upbitws.data_flag and upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units:
                krw_timestamp = upbitws.orderbook[upbitws.codeindex['KRW-BTC']].timestamp
                usd_timestamp = upbitws.orderbook[upbitws.codeindex['USDT-BTC']].timestamp
                for i in range(10):
                    krw_ask = upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].ask_price
                    krw_ask_qty += upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].ask_size
                    if krw_ask_qty * krw_ask > krw_limit:
                        break
                for i in range(10):
                    krw_bid = upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].bid_price
                    krw_bid_qty += upbitws.orderbook[upbitws.codeindex['KRW-BTC']].units[i].bid_size
                    if krw_bid_qty * krw_bid > krw_limit:
                        break
                for i in range(10):
                    usd_ask = upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].ask_price
                    usd_ask_qty += upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].ask_size
                    if usd_ask_qty * usd_ask > usd_limit:
                        break
                for i in range(10):
                    usd_bid = upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].bid_price
                    usd_bid_qty += upbitws.orderbook[upbitws.codeindex['USDT-BTC']].units[i].bid_size
                    if usd_bid_qty * usd_bid > usd_limit:
                        break              
                    upbitws.data_flag = False
                update_flag = True
            upbitws.lock_a.release()
            upbitws.lock_b.release()
            
            #timestamp 차이 10초 미만, 김프 계산식에 사용할 변수들 0이 아닌 경우 진행
            if update_flag:
                if time.time() - krw_timestamp - usd_timestamp < 10 and usd_bid > 0.0 and usd_ask > 0.0 and krw_ask > 0.0 and krw_bid > 0.0 and tb.exchange_rate > 0.0:
                    tb.KRW2USD = (krw_ask - usd_bid * tb.exchange_rate)/(usd_bid * tb.exchange_rate) * 100
                    tb.USD2KRW = (krw_bid - usd_ask * tb.exchange_rate)/(usd_ask * tb.exchange_rate) * 100
                    
                    '''
                    if KRW2USD < KRW2USD_limit: #역프 설정된 값보다 작은 경우, 실행
                        logging.info('KRW2USD')
                    elif USD2KRW > USD2KRW_limit: #김프 설정된 값보다 큰 경우, 실행
                        logging.info('USD2KRW')
                    '''
              
                else:
                    logging.info('Error %d %d %d %f %f %f %f %f'% (time.time() * 2000 - krw_timestamp - usd_timestamp, krw_timestamp,usd_timestamp, usd_bid, usd_ask, krw_ask, krw_bid, tb.exchange_rate))
      

    for t in threading.enumerate():
        if t is not main_thread:
            t.join()
    #tb.get_chance('KRW-BTC')
    #tb.order('USDT-BTC','bid', 11500, 0.0003) #매수
    #tb.order('KRW-BTC','ask', 13000000, 0.0003) #매도
    #tb.order('KRW-BTC','bid', 14000000, 0.0002) #매수
   # tb.get_chance('KRW-BTC')


    # 기본 테스트 환경: xrp, 10원에 100개 구매 (구매 요청 후 취소)
    