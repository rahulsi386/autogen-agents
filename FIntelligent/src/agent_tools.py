from autogen_core.tools import FunctionTool
from services import ExternalFunctions

class AgentTools:
    def __init__(self, ext_func: ExternalFunctions):
        self._ext_func = ext_func

    async def _investor_screener_tool(self) -> FunctionTool:
        return FunctionTool(
            name="investor_screener_tool",
            description="It takes investor's name as input to read investor list.",
            func=self._ext_func._read_investors_list,
            #strict=True,
        )
    
    async def _stocks_screener_tool(self) -> FunctionTool:
        return FunctionTool(
            name="stocks_identifier_tool",
            description="It takes list of sector names as input to identify stocks for each sector.",
            func=self._ext_func._stock_screener,
            #strict=True,
        )
    
    async def _fetch_stocks_data_tool(self) -> FunctionTool:
        return FunctionTool(
            name="fetch_stocks_data",
            description="It takes list of tickers as input to fetch historical data for all the tickers concurrently.",
            func=self._ext_func._fetch_stocks_historical_data,
            #strict=True
        )
        
    async def _market_sentiment_tool(self) -> FunctionTool:
        return FunctionTool(
            name="market_sentiment_tool",
            description="This tool takes list of tickers as input to perform market sentiment analysis.",
            func=self._ext_func._call_bing_grounding,
        )
    
    async def _annual_financial_growth_tool(self) -> FunctionTool:
        return FunctionTool(
            name="annual_financial_growth_tool",
            description="This tool takes list of tickers as input to get annual financial growth data.",
            func=self._ext_func._get_annual_financial_growth_data,
        )
    
    async def _key_metrics_tool(self) -> FunctionTool:
        return FunctionTool(
            name="key_metrics_tool",
            description="This tool takes list of tickers as input to get the annual key metrics data.",
            func=self._ext_func._get_annual_key_metrics_data,
        )
    async def _ratios_ttm_tool(self) -> FunctionTool:
        return FunctionTool(
            name="ratio_ttm_tool",
            description="This tool takes list of tickers as input to get the annual ratio TTM (trailing twelve month) data.",
            func=self._ext_func._get_ratios_ttm_data,
        )

    async def _place_order_tool(self) -> FunctionTool:
        return FunctionTool(
            name="place_order_alpaca",
            description="This tool takes dictionary of ticker symbols and their respective quantities like Dict[str,int] as input to place order using Alpaca API.",
            func=self._ext_func._place_order_alpaca,
            #strict=True
        )
    
    async def _email_notification_tool(self) -> FunctionTool:
        return FunctionTool(
            name="email_notification_tool",
            description="This tool sends email notifications to the user.",
            func=self._ext_func._send_email_notification,
        )
    
    async def _show_portfolio_dashboard_tool(self) -> FunctionTool:
        return FunctionTool(
            name="show_portfolio_dashboard",
            description="Runs a Streamlit Python file (e.g. dashboard.py) to show portfolio dashboard.",
            func=self._ext_func._show_portfolio_dashboard,
        )
