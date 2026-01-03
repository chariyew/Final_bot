import asyncio
import json
import websockets

class TradingViewClient:
    def __init__(self, symbol):
        self.symbol = symbol
        self.price = None

    async def connect(self):
        url = "wss://data.tradingview.com/socket.io/websocket"
        async with websockets.connect(url) as ws:
            session = "qs_" + self.symbol.replace("/", "_")

            await ws.send(json.dumps([
                1,
                "quote_add_symbols",
                {"symbols": [self.symbol], "session": session}
            ]))

            while True:
                msg = await ws.recv()

                try:
                    data = json.loads(msg)
                except:
                    continue

                if isinstance(data, list) and len(data) > 2:
    if "lp" in str(data):
        try:
            self.price = float(
                str(data).split("lp")[1].split(":")[1].split(",")[0]
            )
        except:
            pass


                await asyncio.sleep(0.01)

    def get_price(self):
        return self.price



