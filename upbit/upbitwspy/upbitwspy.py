import asyncio
import websockets
import json

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

class Orderbook:
    code = ''
    timestamp = 0
    units = []

class Orderbook_Unit(object):
    def __init__(self, ask_price, bid_price, ask_size, bid_size):
        self.ask_price = ask_price
        self.bid_price = bid_price
        self.ask_size = ask_size
        self.bid_size = bid_size

class UpbitWebsocket():
    def __init__(self):
        self.uri = "wss://api.upbit.com/websocket/v1"
        self.ticker = Ticker()
        self.orderbook = Orderbook()

    def set_type(self, data_type, codes):
        self.str = '[{"ticket":"hello"},{"type":"%s","codes":["%s"]}]'%(data_type, codes)
    def run(self):
        asyncio.get_event_loop().run_until_complete(self.loop())

    async def loop(self):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(self.str)

            while True:
                data = await websocket.recv()
                ret = json.loads(data)
                #print(ret)
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
                    self.orderbook.code = ret['code']
                    self.orderbook.timestamp = ret['timestamp']
                    self.orderbook.units.clear()
                    for i in range(10):
                        self.orderbook.units.append(Orderbook_Unit(ret['orderbook_units'][i]['ask_price'], ret['orderbook_units'][i]['bid_price'], ret['orderbook_units'][i]['ask_size'], ret['orderbook_units'][i]['bid_size']))



if __name__ == "__main__":
    upbit = UpbitWebsocket()
#    upbit.set_type("ticker","KRW-BTC")
    upbit.set_type("orderbook","KRW-BTC")
    upbit.run()


