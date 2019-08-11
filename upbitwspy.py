import asyncio
import websockets
import json
import threading

class Ticker:
    code = ''
    opening_price = 0.0
    high_price = 0.0
    low_price = 0.0
    trade_price = 0.0
    trade_volume = 0.0
    trade_timestamp = 0
    timestamp = 0 
    def print_data(self):
        print(self.code)

class Orderbook(object):
    def __init__(self, code):
        self.code = ''
        self.mydict = {}
        self.timestamp = 0
        self.units = []

class Orderbook_Unit(object):
    def __init__(self, ask_price, bid_price, ask_size, bid_size):
        self.ask_price = ask_price
        self.bid_price = bid_price
        self.ask_size = ask_size
        self.bid_size = bid_size

class UpbitWebsocket():
    def __init__(self):
        self.lock = threading.Lock()
        self.uri = "wss://api.upbit.com/websocket/v1"
        self.ticker = Ticker()
        self.orderbook = []#Orderbook()
        self.codeindex = {}

    def set_type(self, data_type, codes):
        if data_type == 'orderbook':
            l = len(codes)
            for i in range(l):
                self.orderbook.append(Orderbook(codes[i]))
                self.codeindex[codes[i]] = i
                
        text = ('[{"ticket":"hello"},{"type":"%s","codes":[') % data_type
        i = 1
        l = len(codes)
        for c in codes:    
            text = text + "\"" + c + "\""
            if i != l:
                text = text + ", "
                i = i +1

        text = text + ']}]'
        self.str = text #'[{"ticket":"hello"},{"type":"%s","codes":%s}]'%(data_type, codes)
        print(self.str)

    def run(self):
        myloop = asyncio.new_event_loop()
        asyncio.set_event_loop(myloop)
        myloop.run_until_complete(self.loop())

    async def loop(self):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(self.str)

            while True:
                data = await websocket.recv()
                #print(data)
                ret = json.loads(data)
                #print(ret)
                self.lock.acquire()
                if(ret['type'] == 'ticker'):
                    self.ticker.code = ret['code']
                    self.ticker.opening_price = ret['opening_price']
                    self.ticker.high_price = ret['high_price']
                    self.ticker.low_price = ret['low_price']
                    self.ticker.trade_price = ret['trade_price']
                    self.ticker.trade_volume = ret['trade_volume']
                    self.ticker.trade_timestamp = ret['trade_timestamp']
                    self.ticker.timestamp = ret['timestamp']
                    
                elif(ret['type'] == 'orderbook'): 
                    self.orderbook[self.codeindex[ret['code']]].timestamp = ret['timestamp']
                    self.orderbook[self.codeindex[ret['code']]].units.clear()
                    for i in range(10):
                        self.orderbook[self.codeindex[ret['code']]].units.append(Orderbook_Unit(ret['orderbook_units'][i]['ask_price'], ret['orderbook_units'][i]['bid_price'], ret['orderbook_units'][i]['ask_size'], ret['orderbook_units'][i]['bid_size']))
                #print('DEBUG')
                self.lock.release()



if __name__ == "__main__":
    upbit = UpbitWebsocket()
    upbit.set_type("orderbook",["KRW-BTC","USDT-BTC"])
    upbit.run()
    #t = threading.Thread(target=worker, args=(upbit,))

    #main_thread = threading.currentThread()
#    upbit.set_type("ticker","KRW-BTC")


