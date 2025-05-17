from typing import List, Dict
import os, asyncio, sys, subprocess, time
from concurrent.futures import ThreadPoolExecutor
import requests
import yfinance as yf
import pandas as pd
from azure.ai.projects.models import BingGroundingTool, MessageRole
from dependencymanager import DependencyManager


class ExternalFunctions:
    def __init__(self, dependency_manager: DependencyManager):
        self.dependency_manager = dependency_manager

    @staticmethod
    async def _read_investors_list(self, investor_name: str) -> List[str]:
        try:
            table_client = self.dependency_manager.az_table_client
            query_filter = f"Name eq '{investor_name}'"
            print(f'Query Filter: {query_filter}')
            entities = table_client.query_entities(query_filter=query_filter, select=["Name", "Age", "Risk", "Sectors", "Budget"])
            investors = []
            for entity in entities:
                investor = {
                    "Name": entity["Name"],
                    "Age": entity["Age"],
                    "Risk": entity["Risk"],
                    "Sectors": entity["Sectors"],
                    "Budget": entity["Budget"]
                }
                investors.append(investor)
            return investors
        except Exception as e:
            print(f"Error: {e}")
            

    @staticmethod
    async def _stock_screener(sectors: List[str]):
        stock_screener_base_url = os.getenv("FINANCIAL_MODELING_PREP_BASE_URL")
        stock_screener_api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
        stock_screener_endpoint = f"{stock_screener_base_url}/stock-screener"

        #sector_param = ",".join(sectors) if sectors else None
        responses = []
        for sector in sectors if sectors is not None else []:
            params = {
                "apikey": stock_screener_api_key,
                "sector": sector,
                "isActivelyTrading": "true",
                "exchange": "nyse,nasdaq",
                "limit": 10,
            }
            headers = {
                "Content-Type": "application/json",
            }
            try:
                response = requests.get(stock_screener_endpoint,params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    responses.append(data)
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                print(f"Error: {e}")
                return None
        return responses

    @staticmethod
    async def _get_annual_financial_growth_data(tickers: List[str]):
        stock_screener_api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
        annual_financial_growth_data = []
        try:
            for ticker in tickers:
                request_url = f"https://financialmodelingprep.com/api/v3/financial-growth/{ticker}?period=annual&apikey={stock_screener_api_key}"
                response = requests.get(request_url)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        annual_financial_growth_data.append(data)
                    else:
                        print(f"No data found for {ticker}")
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    return 
            return annual_financial_growth_data
        except Exception as e:
            print(f"Error: {e}")
    
    @staticmethod
    async def _get_annual_key_metrics_data(tickers: List[str]):
        stock_screener_api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
        annual_key_metrics = []
        try:
            for ticker in tickers:
                request_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?period=annual&apikey={stock_screener_api_key}"
                response = requests.get(request_url)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        annual_key_metrics.append(data)
                    else:
                        print(f"No data found for {ticker}")
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    return 
            return annual_key_metrics
        except Exception as e:
            print(f"Error: {e}")

    @staticmethod
    async def _get_ratios_ttm_data(tickers: List[str]):
        stock_screener_api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
        ratios_ttm = []
        try:
            for ticker in tickers:
                request_url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={stock_screener_api_key}"
                response = requests.get(request_url)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        ratios_ttm.append(data)
                    else:
                        print(f"No data found for {ticker}")
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    return 
            return ratios_ttm
        except Exception as e:
            print(f"Error: {e}")

    @staticmethod
    async def _call_bing_grounding(task: str) -> List[str]:
        bing_grounding_tool_conn_name = os.getenv("BING_CONNECTION_NAME")
        try:
            foundry_project_client = dependencymanager.az_ai_foundry_project_client

            bing_conn_id = foundry_project_client.connections.get(connection_name=bing_grounding_tool_conn_name).id
            bing_grounding_tool_definitions = BingGroundingTool(connection_id=bing_conn_id).definitions
            with foundry_project_client:
                agent = foundry_project_client.agents.create_agent(
                    model = os.getenv("OPENAI_MODEL_NAME"),
                    name = "BingGroundingTool",
                    instructions="Get the general market trends, analysts'opinions, or social sentiment, about the stocks.",
                    tools = bing_grounding_tool_definitions,
                    headers = {"x-ms-enable-preview": "true"},
                )
                thread = foundry_project_client.agents.create_thread()
                message = foundry_project_client.agents.create_message(
                    thread_id=thread.id,
                    role = "user",
                    content=task,
                )
                #print(f"Message ID: {message.id}")
                run = foundry_project_client.agents.create_and_process_run(
                    thread_id=thread.id, 
                    agent_id=agent.id,
                    )
                #print(f"Run ID: {run.id}\n Run Status: {run.status}")
                run_steps = foundry_project_client.agents.list_run_steps(run_id=run.id, thread_id=thread.id)
                #run_steps_data = run_steps['data']
                if run.status == "failed":
                    print(f"Run failed with error: {run.error}")
                
                messages = foundry_project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(MessageRole.AGENT)
                messagetext = []
                if messages:
                    for text_message in messages.text_messages:
                        print(f'Agent response: {text_message.text.value}')
                        messagetext.append(text_message.text.value)
                    for annotation in messages.url_citation_annotations:
                        print(f'URL Citation: {annotation.url_citation.title}:{annotation.url_citation.url}')
                return messagetext
        except Exception as e:
            print(f"Error: {e}")
            

    @staticmethod
    async def __fetch_stock_data(ticker:str, period:str="2y"):
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
    @staticmethod
    def __calculate_adj_close(df):
        adjusted_close_price = df['Close'] * (1 + df['Dividends']) * (1 + df['Stock Splits'])
        return adjusted_close_price
    
    @staticmethod
    async def _fetch_stocks_historical_data(tickers:List, period:str="2y"):
        """Fetches historical data for multiple tickers concurrently."""
        try:
            tasks = [ExternalFunctions.__fetch_stock_data(ticker, period) for ticker in tickers]
            results = await asyncio.gather(*tasks)
            # Combine results into a dictionary or multi-index DataFrame
            stock_data_dict = {ticker: df for ticker, df in results if not df.empty}
            # Add 'Adj Close' column to each DataFrame in data_dict
            for ticker, df in stock_data_dict.items():
                df['Adj Close'] = ExternalFunctions.__calculate_adj_close(df)
            
            # Example: Combine 'Adj Close' into a single DataFrame
            adj_close_df = pd.concat(
                {ticker: df['Adj Close'] for ticker, df in stock_data_dict.items()},
                axis=1
            )
            return adj_close_df, stock_data_dict #return data_dict for full OHLCV (Open, High, Low, Close, Volume)
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None, None

    def _show_portfolio_dashboard(filename: str = "dashboard.py"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        #streamlit_url = "http://localhost:8501"
        if not os.path.exists(filepath):
            return f"Error: {filepath} does not exist."
        
        command = [sys.executable, "-m", "streamlit", "run", filepath]
        try:
            process= subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(10)
            """
            try:
                webbrowser.open_new_tab(streamlit_url)
                browser_opened_message = f"Browser opened at {streamlit_url}"
            except Exception as browser_error:
                browser_opened_message = f"Error opening browser: {browser_error}"
                return browser_opened_message
                """
            return f"Attempting to start Streamlit dashboard '{filepath}' in a separate process (PID: {process.pid}). Check your terminal or browser (usually http://localhost:8501)."
        except FileNotFoundError:
            return f"Error: {sys.executable} -m command failed."
        except Exception as e:
            return f"Error running Streamlit: {e}"
        
    @staticmethod
    async def _place_order_alpaca(tickers_with_qty: Dict[str, int]):   
   

        # Initialize API connection
        api = dependencymanager.alpaca_trade_client

        # Check account status
        account = api.get_account()
        print(account.status)
        
        for ticker, qty in tickers_with_qty.items():
            # Check if the ticker is tradable
            ticker = ticker.upper()
            qty = qty if qty else 1 # Default to 1 if qty not specified
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

    async def _send_email_notification():
        try:


            message = {
                "senderAddress": "DoNotReply@c99880a0-5a3c-4694-a642-619e69212f76.azurecomm.net",
                "recipients": {
                    "to": [{"address": "rahulsi@microsoft.com"}]
                },
                "content": {
                    "subject": "Notification from Fintelligent",
                    "plainText": "",
                    "html": """
                        <html>
                        <head>
                            <style>
                                body {
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                }
                                h2 {
                                    color: #2c3e50;
                                }
                                table {
                                    width: 100%;
                                    border-collapse: collapse;
                                    margin-bottom: 20px;
                                }
                                th, td {
                                    border: 1px solid #ddd;
                                    padding: 8px;
                                    text-align: left;
                                }
                                th {
                                    background-color: #f4f4f4;
                                    color: #333;
                                }
                                .section {
                                    margin-bottom: 20px;
                                }
                            </style>
                        </head>
                        <body>
                            <div class="section">
                                <h2>Requirements</h2>
                                <p>
                                    The client is looking for a portfolio that aligns with their investment goals. They prefer a balanced approach with a focus on healthcare, technology, and infrastructure sectors. The total investment amount is $100,000, and the client has a moderate risk appetite.
                                </p>
                            </div>

                            <div class="section">
                                <h2>Portfolio</h2>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Stock</th>
                                            <th>Sector</th>
                                            <th>Allocation (%)</th>
                                            <th>Value ($)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Apple (AAPL)</td>
                                            <td>Technology</td>
                                            <td>20%</td>
                                            <td>20,000</td>
                                        </tr>
                                        <tr>
                                            <td>Pfizer (PFE)</td>
                                            <td>Healthcare</td>
                                            <td>25%</td>
                                            <td>25,000</td>
                                        </tr>
                                        <tr>
                                            <td>Microsoft (MSFT)</td>
                                            <td>Technology</td>
                                            <td>15%</td>
                                            <td>15,000</td>
                                        </tr>
                                        <tr>
                                            <td>Johnson & Johnson (JNJ)</td>
                                            <td>Healthcare</td>
                                            <td>20%</td>
                                            <td>20,000</td>
                                        </tr>
                                        <tr>
                                            <td>Caterpillar (CAT)</td>
                                            <td>Infrastructure</td>
                                            <td>20%</td>
                                            <td>20,000</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            <div class="section">
                                <h2>Order Details</h2>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Stock</th>
                                            <th>Quantity</th>
                                            <th>Price ($)</th>
                                            <th>Total ($)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Apple (AAPL)</td>
                                            <td>10</td>
                                            <td>200</td>
                                            <td>2,000</td>
                                        </tr>
                                        <tr>
                                            <td>Pfizer (PFE)</td>
                                            <td>50</td>
                                            <td>50</td>
                                            <td>2,500</td>
                                        </tr>
                                        <tr>
                                            <td>Microsoft (MSFT)</td>
                                            <td>5</td>
                                            <td>300</td>
                                            <td>1,500</td>
                                        </tr>
                                        <tr>
                                            <td>Johnson & Johnson (JNJ)</td>
                                            <td>20</td>
                                            <td>100</td>
                                            <td>2,000</td>
                                        </tr>
                                        <tr>
                                            <td>Caterpillar (CAT)</td>
                                            <td>10</td>
                                            <td>200</td>
                                            <td>2,000</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            <div class="section">
                                <h2>Additional Info</h2>
                                <p>
                                    The portfolio has been optimized to maximize returns while maintaining a moderate risk profile. The allocation percentages are based on historical performance and market trends.
                                </p>
                                <p>
                                    All orders have been placed successfully, and the portfolio is now active. Please review the details and let us know if any adjustments are required.
                                </p>
                            </div>
                        </body>
                        </html>
                    """
                },
            }
            client = dependencymanager.az_acs_email_client
            poller = client.begin_send(message)
            result = poller.result()
            print(f"Message sent: {result}")

        except Exception as ex:
            print(f"Error sending email: {ex}")
