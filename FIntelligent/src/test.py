import asyncio
import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, AsyncGenerator, List, Sequence
from pypfopt import EfficientFrontier, risk_models, expected_returns
import backtrader as bt
import quantstats
from ib_insync import * # Import necessary classes
import streamlit as st
import alpaca_trade_api as tradeapi
import uuid
from autogen_agentchat.agents import BaseChatAgent, AssistantAgent
from autogen_agentchat.base import Response
from autogen_agentchat.tools import AgentTool, TeamTool
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, TextMessage
from autogen_core import CancellationToken


class CountDownAgent(BaseChatAgent):
    def __init__(self, name: str, count: int =3):
        super().__init__(name, "A simple countdown agent")
        self._count = count

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)
    
    async def on_messages(self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken) -> Response:
        response: Response | None = None
        async for message in self.on_messages_stream(messages, cancellation_token):
            if isinstance(message, Response):
                response = message
            assert response is not None
            return response
        
    async def on_messages_stream(self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        inner_messages: List[BaseAgentEvent | BaseChatMessage] = []
        for i in range(self._count, 0, -1):
            msg = TextMessage(content=f"{i}...", source = self.name)
            inner_messages.append(msg)
            yield msg
        yield Response(chat_message=TextMessage(content="Done!", source = self.name), inner_messages=inner_messages)

    async def on_reset(self, cancellation_token:CancellationToken) -> None:
        pass

    async def run_countdown_agent() -> None:
        countdown_agent = CountDownAgent(name="CountdownAgent", count=3)
        async for message in countdown_agent.on_messages_stream([], CancellationToken()):
            if isinstance(message, Response):
                print(message.chat_message)

            else:
                print(message)
                

async def fetch_ticker_data(ticker, period="2y"):
    """Fetches historical data for a single ticker."""
    loop = asyncio.get_running_loop()
    # Use run_in_executor to run the synchronous yfinance call in a thread pool
    with ThreadPoolExecutor() as pool:
        data = await loop.run_in_executor(
            pool,
            lambda: yf.Ticker(ticker).history(period=period)
        )
    return ticker, data

# Function to calculate adjusted close price
def calculate_adj_close(df):
    adj_close = df['Close'] * (1 + df['Dividends']) * (1 + df['Stock Splits'])
    return adj_close

async def fetch_multiple_tickers(tickers: List, period="2y"):
    """Fetches historical data for multiple tickers concurrently."""
    tasks = [fetch_ticker_data(ticker, period) for ticker in tickers]
    results = await asyncio.gather(*tasks)
    # Combine results into a dictionary or multi-index DataFrame
    data_dict = {ticker: df for ticker, df in results if not df.empty}
    # Add 'Adj Close' column to each DataFrame in data_dict
    for ticker, df in data_dict.items():
        df['Adj Close'] = calculate_adj_close(df)
    
    # Example: Combine 'Adj Close' into a single DataFrame
    adj_close_df = pd.concat(
        {ticker: df['Adj Close'] for ticker, df in data_dict.items()},
        axis=1
    )
    return adj_close_df, data_dict # Or return data_dict for full OHLCV
    
    #return data_dict

async def place_order_alpaca(tickers_with_qty: List[Dict[str,int]]):
    # Replace with your API keys
    API_KEY = 'PKG90HWLVYLYWECQX6VV'
    API_SECRET = 'OCWUeOW8gjoN7qEYpYMdAFnMdHnd8hC0yvXNQlsG'
    BASE_URL = 'https://paper-api.alpaca.markets'

    # Initialize API connection
    api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

    # Check account status
    account = api.get_account()
    print(account.status)

    for item in tickers_with_qty:
        # Check if the ticker is tradable
        ticker = item['ticker']
        qty = item.get('qty', 1)  # Default to 1 if qty not specified
        try:
            asset = api.get_asset(ticker)
            if asset.tradable:
                print(f"{ticker} is tradable.")
            else:
                print(f"{ticker} is not tradable.")
                continue
        except Exception as e:
            print(f"Error fetching asset {ticker}: {e}")
            continue

        # Place a market order for the ticker
        try:
            api.submit_order(
                symbol=ticker,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            print(f"Order placed for {ticker} with quantity {qty}.")
        except Exception as e:
            print(f"Error placing order for {ticker}: {e}")


    # Check the status of the order
    orders = api.list_orders()
    for order in orders:
        print(order)

# To run this async function:
if __name__ == "__main__":
    #print(f"Pandas:{pd.__version__}")	
    #print(f"Quantstats: {quantstats.__version__}")
    #asyncio.run(main_fetch())
    #asyncio.run(place_ib_order())
    tickers_with_qty = [
    {'ticker': 'AAPL', 'qty': 10},
    {'ticker': 'MSFT', 'qty': 5},
    {'ticker': 'GOOGL', 'qty': 2},]
    #asyncio.run(place_order_alpaca(tickers_with_qty))
    #print(uuid.uuid4()) # Generate a unique UUID
    asyncio.run(CountDownAgent.run_countdown_agent())