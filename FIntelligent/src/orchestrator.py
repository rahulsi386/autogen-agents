from autogen_agentchat.teams import MagenticOneGroupChat, SelectorGroupChat, Swarm, BaseGroupChat
from autogen_agentchat.messages import TextMessage, StructuredMessage, HandoffMessage
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination, HandoffTermination
from autogen_agentchat.ui import Console
from colorama import Fore
import os, json, asyncio
from datetime import datetime


# Configure saving chat history to a file
chat_history_dir = "chat_history"
os.makedirs(chat_history_dir, exist_ok=True)
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
chat_history_file = os.path.join(chat_history_dir, f"chathistory_{current_datetime}.txt")

class AgentsOrchestrator:
    def __init__(self):
        self._fintelligent = None
        self._openai_client = az_openai_client

    def _set_fintelligent(self, fintelligent):
        self._fintelligent = fintelligent

    async def fincore_planner(self, task: str):
        #await self._fintelligent._show_portfolio_dashboard_agent()
        reasoning_model = AzureOpenAIChatCompletionClient(
            azure_deployment = os.getenv("OPENAI_REASONING_MODEL_DEPLOYMENT_NAME"),
            model = os.getenv("OPENAI_REASONING_MODEL_NAME"),
            api_version = os.getenv("OPENAI_API_VERSION"),
            azure_endpoint = os.getenv("AZURE_OPENAI_REASONING_ENDPOINT"),
            azure_ad_token_provider = self._fintelligent._token_provider,
        )

        fincore = await self._fintelligent._finCore_planner_agent(reasoning_model_client=reasoning_model)
        #result = await Console(fincore.run_stream(task=task))
        result = await fincore.run(task=task)
        return result.messages

    """
    async def team_magenticone_messages(self, task: str | None = None) -> list:
        \"""
        Runs MagenticOneGroupChat for the given task and returns a list of messages produced by each agent.
        \"""
        websurfer_agent = await self._fintelligent._web_surfer_agent()
        #portfolio_dashboard_agent = await self._fintelligent._show_portfolio_dashboard_agent()
        historical_stock_data_agent = await self._fintelligent._historical_stock_data_agent()
        place_alpaca_order_agent = await self._fintelligent._place_order_alpaca_agent()
        magenticgroupchat_team = MagenticOneGroupChat(
            [websurfer_agent, historical_stock_data_agent, place_alpaca_order_agent],
            model_client=self._openai_client,
        )
        # run and capture TaskResult without streaming to console
        task_result = await magenticgroupchat_team.run(task=task)
        # extract and return the parsed messages
        return task_result.messages
    """
    
    async def selectorgroupchat_team_screener(self, task: str):
        investor_screener_agent = await self._fintelligent._investor_portfolio_screener_agent()
        stock_identifier_agent = await self._fintelligent._stock_identifier_agent()
        termination = TextMentionTermination("TERMINATE")
        selector_prompt = """
        Select an agent to perform task:
        {roles}
        
        Current conversation context:
        {history}

        - When the exection begins, first read the above conversation and then prepare a detailed execution plan with steps to execute.
        - select an agent from {participants} to perform the next task. 
        - To start execution, always select the first agent in {participants} list.
        - Based the last message in the {history} and the overall goal, determine which agent should speak next.
        - Call each agent strictly only once.
        - If the stock identifier agent has returned the names of stocks and its ticker symbol, return the final result and send TERMINATE message.
        """
        selectorgroupchat_team = SelectorGroupChat(
            [investor_screener_agent, stock_identifier_agent], 
            model_client=self._openai_client,
            termination_condition=termination,
            selector_prompt=selector_prompt,
            max_turns=5,
        )
    
        task_result = await Console(selectorgroupchat_team.run_stream(task=task))
        team_state = await selectorgroupchat_team.save_state()
        with open(chat_history_file, "w") as f:
            json.dump(team_state, f, indent=4)
        #print(f'\n\nTask Outcome from Selector Group Chat: {task_result.messages[-1].content}')
        #await self.pore_team_collector(task=task_result.messages[-1].content)
        return task_result.messages
        
              
    # This is a custom multi-agent design pattern that allows for a team of agents to execute in parallel using same input.
    # PORE - Parallel orchestrator engine
    async def pore_team_collector(self, task: str):
        historical_stock_data_agent = await self._fintelligent._historical_stock_data_agent()
        market_sentiment_agent = await self._fintelligent._market_sentiment_analysis_agent()
        annual_financial_growth_agent = await self._fintelligent._annual_financial_growth_agent()
        key_metrics_agent = await self._fintelligent._key_metrics_agent()
        ratios_ttm_agent = await self._fintelligent._ratios_ttm_agent()

        #Run all the agents concurrently and wait for all of them to finish to see results
        results = await asyncio.gather(
            historical_stock_data_agent.run(task=task),
            market_sentiment_agent.run(task=task),
            annual_financial_growth_agent.run(task=task),
            key_metrics_agent.run(task=task),   
            ratios_ttm_agent.run(task=task),
        )

        agent_results_map = {}
        summary_lines = []
        agent_names = ["HistoricalStockDataAgent", "MarketSentimentAgent", "AnnualFinancialGrowthAgent", "KeyMetricsAgent", "RatiosTTMAgent"]
        for i, result in enumerate(results):
            agent_name = agent_names[i]
            agent_message_content = ""
            if result and result.messages:
                agent_message_content = result.messages[-1].content
            agent_results_map[agent_name] = agent_message_content
            print(f"Agent: {agent_name}, content: {agent_message_content}")
            summary_lines.append(f'{agent_name}: {agent_message_content},')

        builder_task_content = "\n".join(summary_lines)
        builder_task_message = TextMessage(content=builder_task_content, source="Syncore")

        #await self.magenticone_team_builder(task=builder_task_message)
        return builder_task_message

    async def pore_team_collector_stream(self, task: str):
        historical_stock_data_agent = await self._fintelligent._historical_stock_data_agent()
        market_sentiment_agent = await self._fintelligent._market_sentiment_analysis_agent()
        annual_financial_growth_agent = await self._fintelligent._annual_financial_growth_agent()
        key_metrics_agent = await self._fintelligent._key_metrics_agent()
        ratios_ttm_agent = await self._fintelligent._ratios_ttm_agent()

        #Run all the agents concurrently and stream results as they come in
        await asyncio.gather(
            Console(historical_stock_data_agent.run_stream(task=task)),
            Console(market_sentiment_agent.run_stream(task=task)),
            Console(annual_financial_growth_agent.run_stream(task=task)),
            Console(key_metrics_agent.run_stream(task=task)),   
            Console(ratios_ttm_agent.run_stream(task=task)),
        )

    async def magenticone_team_builder(self, task: list):
        portfolio_builder_agent = await self._fintelligent._portfolio_builder_agent()
        final_answer_prompt = """
        Find out all the tickers and their corresponding approx_quantity values and return them as a dictionary.
        """
        magenticgroupchat_team = MagenticOneGroupChat(
            [portfolio_builder_agent], 
            model_client=self._openai_client,
            final_answer_prompt=final_answer_prompt,
            max_turns = 3,
            termination_condition=TextMentionTermination("TERMINATE"),	
        )
        task_result = await Console(magenticgroupchat_team.run_stream(task=task))
        print(f'\n\nTask Outcome from MagenticOneGroupChat: {task_result.messages[-1].content}')
        team_state = await magenticgroupchat_team.save_state()
        with open(chat_history_file, "w") as f:
            json.dump(team_state, f, indent=4)
        #await self.swarm_team_executor(task=task_result.messages[-1].content)
        return task_result.messages

    async def swarm_team_executor(self, task: str):
        trading_agent = await self._fintelligent._trading_agent()
        termination = HandoffTermination(target="user") | TextMentionTermination("TERMINATE")
        swarm_team = Swarm([trading_agent], termination_condition=termination, max_turns=3)
        task_result = await Console(swarm_team.run_stream(task=task))
        last_message = task_result.messages[-1]
        #print(Fore.LIGHTCYAN_EX + f"Task Outcome: {task_result.messages}")
        while isinstance(last_message, HandoffMessage) and last_message.target == "user":
            user_message = input(Fore.YELLOW + "User: " + Fore.RESET)
            task_result = await Console(swarm_team.run_stream(task=HandoffMessage(source="user", content=user_message, target=last_message.source)))
            last_message = task_result.messages[-1]
        print(Fore.LIGHTCYAN_EX + f"Task Outcome: {last_message.content}")