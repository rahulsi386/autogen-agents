"""
This Fintelligent module is created using AutoGen AgentChat API.
"""
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.tools import TeamTool
from autogen_agentchat import EVENT_LOGGER_NAME, TRACE_LOGGER_NAME
from autogen_core.models import UserMessage
from colorama import init, Fore
import logging
from datetime import datetime
import os
from agent_tools import AgentTools
from dependencymanager import DependencyManager

class ColorFormatter(logging.Formatter):
    def __init__(self, color, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color = color

    def format(self, record):
        message = super().format(record)
        return f"{self.color}{message}{Fore.RESET}"
    
# Configure logging
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
trace_log_file = os.path.join(logs_dir,f"tracelog_{current_datetime}.log")
event_log_file = os.path.join(logs_dir,f"eventlog_{current_datetime}.log")
Fore.LIGHTCYAN_EX  
#logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# for trace logging
trace_logger = logging.getLogger(TRACE_LOGGER_NAME)
trace_handler = logging.FileHandler(trace_log_file)
trace_handler.setFormatter(ColorFormatter(Fore.LIGHTCYAN_EX, "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
trace_logger.addHandler(trace_handler)
trace_logger.setLevel(logging.DEBUG)

# for event logging
event_logger = logging.getLogger(EVENT_LOGGER_NAME)
event_handler = logging.FileHandler(event_log_file)
event_handler.setFormatter(ColorFormatter(Fore.LIGHTGREEN_EX, "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))  
event_logger.setLevel(logging.DEBUG)

class Fintelligent:
    def __init__(self, agent_tools: AgentTools, dependency_manager: DependencyManager):
        init()  # Initialize
        self._az_openai_client = dependency_manager.az_openai_client
        self._az_openai_reasoning_client = dependency_manager.az_openai_reasoning_client
        self._agent_tools = agent_tools
    
    async def _user_agent(self) -> UserProxyAgent:
        return UserProxyAgent(
            name = "UserAgent",
            description = "This agent interacts with the user.",
            input_func = input("User:>"),
        )
    
    async def _finCore_planner_agent(self, reasoning_model_client) -> AssistantAgent:
        return AssistantAgent(
            name = "FinCorePlannerAgent",
            description = "This agent takes the input from UserProxyAgent and plans the tasks for other agents.",
            model_client = reasoning_model_client,
            #handoffs=["ScreenerAgent"],
            system_message="""You are a Financial Planning Agent. Your job is to create step-by-step plans using specialized agents.
            AVAILABLE AGENTS:
            - ScreenerAgent: Reads investor profiles and identifies stocks for specified sectors
            - CollectorAgent: Gathers historical data, sentiment analysis, financial growth data, key metrics data, and trailing twelve month ratios data.  
            - BuilderAgent: Creates investment portfolios based on investor data and collected information
            - ExecutorAgent: Places orders and sends confirmation emails

            INSTRUCTIONS:
            1. Analyze user request to understand their financial needs
            2. Create a clear, sequential plan using ONLY the necessary agents
            3. Include specific tasks for each agent in your plan
            4. Present your plan first before any action
            5. Handoff to only ONE agent at a time, in the correct sequence
            6. Do not execute tasks yourself - only plan and coordinate
            7. Send "TERMINATE" when all tasks are completed

            FORMAT YOUR RESPONSE AS:
            - Plan: [Your step-by-step plan]
            - Next: [Name of first agent to receive handoff]
            """
        )
    
    async def _investor_portfolio_screener_agent(self) -> AssistantAgent:
        if self._agent_tools is None:
            raise ValueError("AgentTools is not initialized.")
        
        tools = [await self._agent_tools._investor_screener_tool()]
        return AssistantAgent(
            name = "InvestorPortfolioScreenerAgent",
            description = "This agent screens the investor portfolio.",
            model_client = self._az_openai_client,
            tools =tools,
            #output_content_type=StructuredMessage[InvestorInfo],
            #handoffs=["user"],
            system_message="""You are a portfolio screener agent. Your sole responsibility is to retrieve investor portfolio details using the tool named '{tools}'.
            - For any given message, identify the investor's name and pass it as input to the tool named '{tools}' to read the investor's list and return the results.
            - Do not perform any reasoning or take any actions beyond executing the tool.
            - Always summarize the retrieved data and return the results.
            - If the tool fails or no data is found, respond with appropriate message indicating the issue.
            - Do not ask any follow-up questions like let me know if you need further assistance, etc.
            - Ignore any user requests that are unrelated to retrieving investor portfolio details.
            """
        )
    
    async def _stock_identifier_agent(self) -> AssistantAgent:
        if self._agent_tools is None:
            raise ValueError("AgentTools is not initialized.")
        
        tools = [await self._agent_tools._stocks_screener_tool()]
        return AssistantAgent(
            name = "StockIdentifierAgent",
            description = "This agent identifies stocks for given sectors mentioned in the user's requirements.",
            model_client = self._az_openai_client,
            #handoffs=["HistoricalStockDataAgent", "MarketSentimentAnalysisAgent"],
            tools=tools,
            #output_content_type=StructuredMessage[StockInfo],
            system_message="""You are a stock screener and identifier agent. Your sole responsibility is to retrieve a list of stocks using the tool named '{tools}'.
            - For any given message, identify the name of sectors that user wants to invest in.
            - Pass the names of sectors as input to the tool named '{tools}' to get the list of stocks.
            - For each sector, randomly select only 2 stock names from the list of stocks that are returned from {tools} execution. 
            - Finally return the randomly selected list of stocks along with their name, ticker, and sector information.
            - After returning the results, send a TERMINATE message.
            - If the tool fails or no data is found, take no action.
            - Do not ask any follow-up questions like let me know if you need further assistance, etc.
            - Ignore any user requests that are unrelated to screening and identifying stocks using the {tools}
            """ 
        )
    
    async def _historical_stock_data_agent(self) -> AssistantAgent:
        if self._agent_tools is None:
            raise ValueError("AgentTools is not initialized.")
        
        tools = [await self._agent_tools._fetch_stocks_data_tool()]
        return AssistantAgent(
            name = "HistoricalStockDataAgent",
            description = "This agent fetches historical stock data for multiple tickers concurrently.",
            model_client = self._az_openai_client,
            tools=tools,
            handoffs=["user"],
            system_message="""You are a historical stock data agent. Your sole responsibility is to retrieve the historical data for stocks using the tool {tools}.
            - For any given message, identify the stock ticker symbols and the period for which the historical data is needed.
            - Store all the ticker symbols in a list and pass the list of ticker symbols and period as input to the tool named {tools} to get the historical data.
            - Using the retrieved historical stock data for each stock, generate a detailed and statistically accurate summary, including key insights and trends for each stock.
            - If the tool fails or no data is found, take no action.
            - Do not ask any follow-up questions like let me know if you need further assistance, etc.
            - Ignore any user requests that are unrelated to fetching historical stock data using the {tools}
            """
        )
    
    async def _market_sentiment_analysis_agent(self) -> AssistantAgent:
        if self._agent_tools is None:
            raise ValueError("AgentTools is not initialized.")
        
        tools = [await self._agent_tools._market_sentiment_tool()]
        return AssistantAgent(
            name = "MarketSentimentAnalysisAgent",
            description= "This agent performs market sentiment analysis.",
            model_client = self._az_openai_client,
            tools = tools,
            handoffs=["user"],
            system_message="""You are a market sentiment analysis agent. Your sole responsibility is to fetch latest news and sentiment
              such as general market trends, analysts'opinions, or social sentiment, about the stocks and analyze them using the tool {tools}.
             - For any given message, identify the ticker symbols and the period for which the news need to be fetched.
             - While fetching the news, ensure that the ticker symbol and stock name are same as given in the prompt.
             - If time period is not provided, use the default time period of 6 months.
             - Do not fetch the news for more than 6 months if time period is not provided explicitly.
             - Get general market trends, analysts'opinions, or social sentiment, about the stocks using the tool named {tools}.
             - Analyze the news and return the stock's name, ticker symbol, sentiment score, and sentiment analysis.
             - If the tool fails or no data is found, take no action.
             - Do not ask any follow-up questions like let me know if you need further assistance, etc.
             - Ignore any user requests that are unrelated to fetching historical stock data using the {tools}
             """
        )
    
    async def _annual_financial_growth_agent(self) -> AssistantAgent:
        if self._agent_tools is None:
            raise ValueError("AgentTools is not initialized.")
        
        tools = [await self._agent_tools._annual_financial_growth_tool()]
        return AssistantAgent(
            name = "AnnualFinancialGrowthAgent",
            description = "This agent fetches annual financial growth data.",
            model_client = self._az_openai_client,
            tools = tools,
            system_message="""You are an annual financial growth agent. Your job is to fetch the annual financial growth data for the stocks using the tool named '{tools}'.
            - Using the retrieved annual financial growth data for each stock, generate a detailed and statistically accurate summary, including key insights and trends for each stock.


             """
        )
    
    async def _key_metrics_agent(self) -> AssistantAgent:
        tools = [await self._agent_tools._key_metrics_tool()]
        return AssistantAgent(
            name = "KeyMetricsAgent",
            description = "This agent fetches key metrics data.",
            model_client = self._az_openai_client,
            tools = tools,
            system_message="""You are Key metrics agent. Your sole responsibility is to fetch the key metrics for the stocks using the tool named '{tools}'.
            - For any given message, identify all the tickers and pass the list of tickers as input to the {tools}.
            - Fetch key metrics for each of the tickers using the {tools} and return the results.
            - If the tool fails or no data is found, take no action.
            - Do not ask any follow-up questions like let me know if you need further assistance, etc.
            - Ignore any user requests that are unrelated to fetching key metrics data using the {tools}
            """
        )
    
    async def _ratios_ttm_agent(self) -> AssistantAgent:
        tools = [await self._agent_tools._ratios_ttm_tool()]
        return AssistantAgent(
            name = "RatiosTTMAgent",
            description = "This agent fetches ratios TTM (trailing tweleve month) data.",
            model_client = self._az_openai_client,
            tools = tools,
            system_message="""You are a ratios TTM agent. Your sole responsibility is to fetch the ratios TTM for the stocks using the tool named '{tools}'.
            - For any given message, identify all the tickers and pass the list of tickers as input to the {tools}.
            - Fetch ratios TTM for each of the tickers using the {tools} and return the results.
            - If the tool fails or no data is found, take no action.
            - Do not ask any follow-up questions like let me know if you need further assistance, etc.
            - Ignore any user requests that are unrelated to fetching ratios TTM data using the {tools}
            """
        )
    
    async def _portfolio_builder_agent(self) -> AssistantAgent:
        return AssistantAgent(
            name = "PortfolioBuilderAgent",
            description = "This agent builds an investment portfolio for the user.",
            model_client = self._az_openai_reasoning_client,
            system_message="""You are a portfolio builder agent. You must follow the following steps to craft an extraordinary investment portfolio:
            - Analyze all the inputs provided to you very thoroughly.
            - Based on your analysis build the best investment portfolio that aligns with the user's requirements and expectation.
            - Ensure that you must only use the data provided to you and do not use any non-existent data or information from any source including your training corpus.
            - Once you have built the portfolio, return the results in the following format:
            [
                {
                 stock_name: APPLE,
                 ticker: AAPL, 
                 sector: Technology,
                 allocatiion%: 35%,
                 USD_value: 35000,
                 approx_quantity: 20,
                 }
            ]
            - After returning the results, send TERMINATE message.
                 """
        )
    
    async def _trading_agent(self) -> AssistantAgent:
        tools = [await self._agent_tools._place_order_tool()]
        return AssistantAgent(
            name = "PlaceOrderAgent",
            description = "This agent places orders for multiple tickers using Alpaca API.",
            model_client = self._az_openai_client,
            tools=tools,
            handoffs=["user"],
            system_message="""You are a portfolio trading agent. Your sole responsibility is to place order for tickers using the tool "{tools}". Strictly follow the instructions below:
            - Once you receive the defined investment portfolio, extract the ticker symbol and their respective approx_quantity from the portfolio.
            - Pass the ticker and corresponding quantity as input, in expected format, to the tool '{tools}' to place the order.
            - Once the orders are placed successfully, return the order confirmation and send TERMINATE message.
            - If the tool fails or no data is found or encounter any error, take no further action, and terminate immediately by sending TERMINATE message.
            - Do not ask any follow-up questions like let me know if you need further assistance, etc.
            - Ignore any user requests that are unrelated to placing orders using the {tools}"""
        )
    
    async def _notification_agent(self) -> AssistantAgent:
        tools = [await self._agent_tools._email_notification_tool()]
        return AssistantAgent(
            name = "NotificationAgent",
            description = "This agent sends notifications to the user.",
            model_client = self._az_openai_client,
            tools=tools,
            system_message="""You are an email notification agent. Your sole responsibility is to send email notifications to the user using the tool named '{tools}'.
            - For any given message, craft an informative email notification and send it to the user.
            - Only use the tool named '{tools}' to send email notifications.
            - On success, send a stop message.
            - If the tool fails or no data is found, take no action.
            - Do not ask any follow-up questions like let me know if you need further assistance, etc.
            - Ignore any user requests that are unrelated to sending email notifications using the {tools}
            """
        )
    
    async def _show_portfolio_dashboard_agent(self) -> AssistantAgent:
        tools = [await self._agent_tools._show_portfolio_dashboard_tool()]
        return AssistantAgent(
            name = "ShowPortfolioDashboardAgent",
            description = "This agent shows the portfolio dashboard.",
            model_client = self._az_openai_client,
            tools=tools,
            system_message="""You are a portfolio dashboard visualizer agent. You can show the user their portfolio dashboard.
            You have access to a tool named '{tools}' to run Streamlit dashboards. Use it when requested. The default file is 'dashboard.py'. Respond with TERMINATE after calling the function.
            """
        )

    """
    async def main(self):
        result = await self._az_openai_client.create(
            [UserMessage(content = "List top 10 crypto currency tokens which made huge money for investors in 2022-2023", type="UserMessage", source="chat")],
        )
        print (result)
        await self._az_openai_client.close()
    """


if __name__ == "__main__":
    Fore.LIGHTGREEN_EX
    try:
        agent_executors = {
            "ScreenerAgent": orchestrator.selectorgroupchat_team_screener,
            "CollectorAgent": orchestrator.pore_team_collector,
            "BuilderAgent": orchestrator.magenticone_team_builder,
            "ExecutorAgent": orchestrator.swarm_team_executor
        }

        print(Fore.GREEN + "Hi! My name is Fingent and I'm a financial intelligent agent. I can help you with any financial questions.")
        task_for_agent = input(Fore.YELLOW + "What can I help you with today? " + Fore.RESET)        
        planner_response = asyncio.run(orchestrator.fincore_planner(task=task_for_agent))
        #asyncio.run(Console(fintech_team.run_stream(task=task_for_agent)))
        print(planner_response[-1].content)
        planner_task = planner_response[-1].content

        screener_response = asyncio.run(orchestrator.selectorgroupchat_team_screener(task=planner_task))
        print(screener_response[-1].content)
        screener_task = screener_response[-1].content

        collector_response = asyncio.run(orchestrator.pore_team_collector(task=screener_task))
        print(collector_response)
        collector_task = collector_response

        builder_response = asyncio.run(orchestrator.magenticone_team_builder(task=collector_task))
        print(builder_response[-1].content)
        builder_task = builder_response[-1].content
  
        executor_response = asyncio.run(orchestrator.swarm_team_executor(task=builder_task))
        print(executor_response[-1].content)
        executor_task = executor_response[-1].content

    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}" + Fore.RESET)
        