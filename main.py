import os
import asyncio
import json
import alpaca_trade_api as tradeapi
import openai
import logging
import websocket

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
BASE_URL = os.environ.get("BASE_URL")

logging.basicConfig(level=logging.INFO)

openai.api_key = os.environ.get('OPENAI_API_KEY')
openai.default_headers = {"x-foo": "true"}

def chatgptCompletitions(last_news):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system", 
                "content": "Only respond with a number from 1-100 detailing the impact of the news headline and summary, and the sentiment as positive or negative in json format with key impact and sentiment"
            }, {
                "role": "assistant", 
                "content": "Given the headline '" + last_news["headline"] + "' and the summary '" + last_news["summary"] + "', show me a number from 1-100 detailing the impact of this headline and summary and the sentiment as positive or negative in json format with key impact and sentiment"
            }
        ]
    )
    return completion

def on_message(ws, message):
    # This function will be called when a message is received
    news_data = json.loads(message)
    print("Received news update:", news_data)
    for news in news_data:
        # news = {
        #     "T": "n",
        #     "id": 24918784,
        #     "headline": "Corsair Reports Purchase Of Majority Ownership In iDisplay, No Terms Disclosed",
        #     "summary": "Corsair Gaming, Inc. (NASDAQ:CRSR) (“Corsair”), a leading global provider and innovator of high-performance gear for gamers and content creators, today announced that it acquired a 51% stake in iDisplay",
        #     "author": "Benzinga Newsdesk",
        #     "created_at": "2022-01-05T22:00:37Z",
        #     "updated_at": "2022-01-05T22:00:38Z",
        #     "url": "https://www.benzinga.com/m-a/22/01/24918784/corsair-reports-purchase-of-majority-ownership-in-idisplay-no-terms-disclosed",
        #     "content": "\u003cp\u003eCorsair Gaming, Inc. (NASDAQ:\u003ca class=\"ticker\" href=\"https://www.benzinga.com/stock/CRSR#NASDAQ\"\u003eCRSR\u003c/a\u003e) (\u0026ldquo;Corsair\u0026rdquo;), a leading global ...",
        #     "symbols": ["CRSR"],
        #     "source": "benzinga"
        # }
        if news["T"] == "n":
            api = tradeapi.REST(key_id=ALPACA_API_KEY, 
                                secret_key=ALPACA_SECRET_KEY, 
                                base_url=BASE_URL, api_version='v2')
            # Check open orders
            open_orders = api.list_orders(status='open')
            open_orders_symbols = [x.symbol for x in open_orders]

            for symbol in news["symbols"]:
                
                # IGNORE IF WE ALREADY HAVE AN ORDER
                if symbol in open_orders_symbols:
                    logging.warning(f"Ignoring BUY signal for {symbol}, as there is already an open position for this symbol in the account with news {news}.")
                    continue
                logging.info(f"New news {news}")       
                chatGPT_response = chatgptCompletitions(last_news=news)
                chatGPT_response_json = json.loads(chatGPT_response.choices[0].message.content)
                logging.info(f"ChatGPT Response {chatGPT_response_json}")       


                account = api.get_account()
                # 500 or Ticker price if gt than 500
                latest_trade = api.get_latest_trade(symbol)
                side = "buy" if chatGPT_response_json["sentiment"] == "positive" else "sell"
                qty=500 // latest_trade.price
        
                buying_price = latest_trade.price if latest_trade.price > 500 else qty * latest_trade.price
        
                # IF NEWS IMPACT GT 75
                if float(account.buying_power) > buying_price and chatGPT_response_json["impact"] > 75:
                    response = api.submit_order(
                        symbol=symbol,
                        qty=qty,
                        side=side,
                        type='market',
                        time_in_force='gtc'
                    )
                    logging.info(f"Order id {response.id} for ticker {response.symbol} created, buy power: {account.buying_power}, qty {qty}, order price {qty * latest_trade.price} ")
                else: 
                    logging.warning(f"Ignoring {side} signal, buy power: {account.buying_power}, qty {qty}, order price {qty * latest_trade.price} ")

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, message, error):
    print("### Connection Closed ###")

def on_open(ws):
    print("Connection Opened")
    # Open the file and load it into a Python dictionary
    with open('tickers.json', 'r') as file:
        tickers_dict = json.load(file)
    ticker_symbols = [item["tickerSymbol"] for item in tickers_dict]
    ws.send(json.dumps({"action":"auth","key":ALPACA_API_KEY,"secret":ALPACA_SECRET_KEY}))
    ws.send(json.dumps({"action":"subscribe","news":ticker_symbols}))

if __name__ == "__main__":

    # Alpaca's real-time news WebSocket endpoint
    websocket_url = "wss://stream.data.alpaca.markets/v1beta1/news"
    ws = websocket.WebSocketApp(websocket_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()

