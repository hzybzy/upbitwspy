import asyncio
import websockets


class UpbitWebsocket():
	def __init__(self):
		self.uri = "wss://api.upbit.com/websocket/v1"

	def set_type(self, data_type, codes):
		self.str = '[{"ticket":"hello"},{"type":"%s","codes":["%s"]}]'%(data_type, codes)
	def run(self):
		asyncio.get_event_loop().run_until_complete(self.loop())
		

	async def loop(self):
		async with websockets.connect(self.uri) as websocket:
			await websocket.send(self.str)

			while True:
				greeting = await websocket.recv()
				print(f"< {greeting}")


if __name__ == "__main__":
	upbit = UpbitWebsocket()
	upbit.set_type("ticker","KRW-BTC")
	upbit.run()


