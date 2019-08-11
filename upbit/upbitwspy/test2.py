import threading
import upbitwspy
import time
import requests #for real currency rate
import json #for real currency rate

def worker(upbit):
    print('start worker')
    upbit.set_type("orderbook",["KRW-BTC","USDT-BTC"])
    upbit.run()

def get_real_currency():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = 'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD'
    exchange =requests.get(url, headers=headers).json()
    #TODO : tracking date "date":"2019-08-09","time":"20:01:00"
    return exchange[0]['basePrice']

if __name__ == "__main__":
    currency_rate = get_real_currency()
    
    upbit = upbitwspy.UpbitWebsocket()
    t = threading.Thread(target=worker, args=(upbit,))
    t.start()
    
    main_thread = threading.currentThread()
    #김프 공식 : (국내-해외)/해외 * 100
    #ask_price : 매도
    #bid_price : 매수
    #Direction (시장가 거래 기준)
    #원화 -> BTC -> 달러 : (국내_ask-해외_bid)/해외_bid * 100
    #달러 -> BTC -> 원화 : (국내_bid-해외_ask)/해외_ask * 100
    while True:
        
        if upbit.codeindex:
            #krw_ask = 0.0
            #krw_bid = 0.0
            krw_ask_qty = 0.0
            krw_bid_qty = 0.0
            #usd_ask = 0.0
            #usd_bid = 0.0
            usd_ask_qty = 0.0
            usd_bid_qty = 0.0
            krw_limit = 50000
            usd_limit = krw_limit / currency_rate
            
            upbit.lock.acquire()
            if upbit.orderbook[upbit.codeindex['KRW-BTC']].units:
                
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

            upbit.lock.release()
            #print("KRW-BTC %d %d"%(krw_ask, krw_bid))
            #print("USDT-BTC %f %f"%(usd_ask, usd_bid))
            print("원화->달러 : %.3f"%((krw_ask - usd_bid*currency_rate)/(usd_bid*currency_rate) * 100))
            print("달러->원화 : %.3f"%((krw_bid - usd_ask*currency_rate)/(usd_ask*currency_rate) * 100))
        time.sleep(1)

    for t in threading.enumerate():
        if t is not main_thread:
            t.join()

