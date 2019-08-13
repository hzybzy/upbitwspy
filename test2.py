import threading
import upbitwspy
import time
import requests #for real currency rate
import json #for real currency rate
import logging
import platform

exchange_rate = 0.0
KRW2USD_limit = -3.0 #역프 때 이득
USD2KRW_limit = 0.0 #김프 때 이득
KRW2USD = 0.0
USD2KRW = 0.0

def worker_get_orderbook(upbit):
    #start worker
    upbit.set_type("orderbook",["KRW-BTC","USDT-BTC"])
    upbit.run()


def worker_exchange_rate():
    while True:
        time.sleep(1000)
        exchange_rate = get_real_currency()
        logging.info('exchange rate was updated %.2f'%exchange_rate)

def worker_logger():
    while True:        
        text = 'KRW2USD, USD2KRW, %.3f, %.3f' % (KRW2USD, USD2KRW)#, krw_timestamp/1000, usd_timestamp/1000, time.time())                
        #text = '%d ask : %f %f bid : %f %f'% (usd_timestamp/1000, usd_ask, usd_ask_qty, usd_bid, usd_bid_qty)
        logging.info(text)
        time.sleep(1)
        #time.sleep(1)

def get_real_currency():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = 'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD'
    try:
        ret =requests.get(url, headers=headers).json()
    except:
        return 0
    #TODO : tracking date "date":"2019-08-09","time":"20:01:00"
    return ret[0]['basePrice']

if __name__ == "__main__":

    if platform.system() == 'Linux':
        logging.basicConfig(filename='test.log', format='%(asctime)s, %(message)s', level=logging.INFO, datefmt='20%y-%m-%d %H:%M:%S')
    else:       # equal 'Windows'
        logging.basicConfig(format='%(asctime)s, %(message)s', level=logging.INFO, datefmt='20%y-%m-%d %H:%M:%S')
    exchange_rate = get_real_currency()
    logging.info('exchange rate was updated %.2f'%exchange_rate)


    upbit = upbitwspy.UpbitWebsocket()

    t1 = threading.Thread(target=worker_get_orderbook, args=(upbit,))
    t1.start()

    t2 = threading.Thread(target=worker_exchange_rate)
    t2.start()

    t3 = threading.Thread(target=worker_logger)
    t3.start()
        
    main_thread = threading.currentThread()
    #김프 공식 : (국내-해외)/해외 * 100
    #ask_price : 매도
    #bid_price : 매수
    #Direction (시장가 거래 기준)
    #원화 -> BTC -> 달러 : (국내_ask-해외_bid)/해외_bid * 100 // 낮은게 좋아
    #달러 -> BTC -> 원화 : (국내_bid-해외_ask)/해외_ask * 100 // 높은게 좋아
    
    while True:
        if upbit.codeindex:
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
            if exchange_rate:
                usd_limit = krw_limit / exchange_rate
            
            krw_timestamp = 0.0
            usd_timestamp = 0.0
            
            
            update_flag = False
            upbit.lock.acquire()
            
            if upbit.data_flag and upbit.orderbook[upbit.codeindex['KRW-BTC']].units:
                krw_timestamp = upbit.orderbook[upbit.codeindex['KRW-BTC']].timestamp
                usd_timestamp = upbit.orderbook[upbit.codeindex['USDT-BTC']].timestamp
                for i in range(10):
                    krw_ask = upbit.orderbook[upbit.codeindex['KRW-BTC']].units[i].ask_price
                    krw_ask_qty += upbit.orderbook[upbit.codeindex['KRW-BTC']].units[i].ask_size
                    if krw_ask_qty * krw_ask > krw_limit:
                        break
                for i in range(10):
                    krw_bid = upbit.orderbook[upbit.codeindex['KRW-BTC']].units[i].bid_price
                    krw_bid_qty += upbit.orderbook[upbit.codeindex['KRW-BTC']].units[i].bid_size
                    if krw_bid_qty * krw_bid > krw_limit:
                        break
                for i in range(10):
                    usd_ask = upbit.orderbook[upbit.codeindex['USDT-BTC']].units[i].ask_price
                    usd_ask_qty += upbit.orderbook[upbit.codeindex['USDT-BTC']].units[i].ask_size
                    if usd_ask_qty * usd_ask > usd_limit:
                        break
                for i in range(10):
                    usd_bid = upbit.orderbook[upbit.codeindex['USDT-BTC']].units[i].bid_price
                    usd_bid_qty += upbit.orderbook[upbit.codeindex['USDT-BTC']].units[i].bid_size
                    if usd_bid_qty * usd_bid > usd_limit:
                        break              
                upbit.data_flag = False
                update_flag = True
            upbit.lock.release()
            
            #timestamp 차이 10초 미만, 김프 계산식에 사용할 변수들 0이 아닌 경우 진행
            if update_flag:
                if time.time() - krw_timestamp - usd_timestamp < 10 and usd_bid > 0.0 and usd_ask > 0.0 and krw_ask > 0.0 and krw_bid > 0.0 and exchange_rate > 0.0:
                    KRW2USD = (krw_ask - usd_bid*exchange_rate)/(usd_bid*exchange_rate) * 100
                    USD2KRW = (krw_bid - usd_ask*exchange_rate)/(usd_ask*exchange_rate) * 100
                    
                    '''
                    if KRW2USD < KRW2USD_limit: #역프 설정된 값보다 작은 경우, 실행
                        logging.info('KRW2USD')
                    elif USD2KRW > USD2KRW_limit: #김프 설정된 값보다 큰 경우, 실행
                        logging.info('USD2KRW')
                    '''
              
                else:
                    logging.info('Error %d %d %d %f %f %f %f %f'% (time.time() * 2000 - krw_timestamp - usd_timestamp, krw_timestamp,usd_timestamp, usd_bid, usd_ask, krw_ask, krw_bid, exchange_rate))
      

    for t in threading.enumerate():
        if t is not main_thread:
            t.join()
