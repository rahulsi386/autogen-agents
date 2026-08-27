import asyncio
from configmanager import ConfigurationManager, ConfigurationProvider
from dependencymanager import DependencyManager
from services import ExternalFunctions
from agent_tools import AgentTools
from autogen_agentchat.ui import Console
from agents import Fintelligent
import pandas as pd

async def main():
    config_manager = ConfigurationManager()
    config_provider = ConfigurationProvider(config_manager)
    dependency_manager = DependencyManager(config_provider=config_provider)
    services = ExternalFunctions(dependency_manager=dependency_manager)
    agent_tools = AgentTools(ext_func=services)
    fintelligent = Fintelligent(agent_tools=agent_tools, dependency_manager=dependency_manager)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)

   # ---------------------------------------------------------------------
   # TESTING External Functions
   # ---------------------------------------------------------------------
    #investor_info = await services._read_investors_list(investor_name="Graham")
    #print(investor_info)
    #stocks = await services._stock_screener(sectors = ["Energy", "Healthcare"])
    #for stock in stocks:
    #    print(stock) 
   # afgds = await services._get_annual_financial_growth_data(tickers=["AAPL"])
   # [print(afgd) for afgd in afgds]
   # akmds = await services._get_annual_key_metrics_data(tickers=["AAPL"])
   # [print(akmd) for akmd in akmds]
   # rttms = await services._get_ratios_ttm_data(tickers=["AAPL"])
   # [print(rttm) for rttm in rttms]
   # bing = await services._call_bing_grounding(task = "find the latet news about Microsoft")
   # [print(b) for b in bing]
   # adj_close, histdata = await services._fetch_stocks_historical_data(tickers=["AAPL", "MSFT"])
   # print(f'Adj Close: {adj_close}\n Historical Data: {histdata}')
   # orders = await services._place_order_alpaca(tickers_with_qty={"MARA": 1},)
   # for order in orders:
   #     print(f"{order}") 

   # ---------------------------------------------------------------------
   # TESTING Agents and Tools
   # ---------------------------------------------------------------------
   # investor_screener_agent = await fintelligent._investor_portfolio_screener_agent()
   # await Console(investor_screener_agent.run_stream(task = "Need information on Graham"))
   # stock_agent = await fintelligent._stock_identifier_agent()
   # await Console(stock_agent.run_stream(task = "get me top 10 stocks in healthcare"))
   # historical_data_agent = await fintelligent._historical_stock_data_agent()
   # await Console(historical_data_agent.run_stream(task = "get me historical data for AAPL"))
   # sentiment_agent = await fintelligent._market_sentiment_analysis_agent()
   # await Console(sentiment_agent.run_stream(task = "I want to understand the market position of Amazon"))
   # financial_growth_agent = await fintelligent._annual_financial_growth_agent()
   # await Console(financial_growth_agent.run_stream(task = "get me annual financial growth data for AAPL"))
   # keymetrics_agent = await fintelligent._key_metrics_agent()
   # await Console(keymetrics_agent.run_stream(task = "get me annual key metrics data for MSFT"))
    ttm_agent = await fintelligent._ratios_ttm_agent()
    await Console(ttm_agent.run_stream(task = "get me annual ratios ttm data for Amazon"))



if __name__ == "__main__":
    asyncio.run(main())
