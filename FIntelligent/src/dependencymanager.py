from autogen_ext.auth.azure import AzureTokenProvider
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.data.tables import TableServiceClient
from azure.communication.email import EmailClient
from azure.ai.projects import AIProjectClient
import alpaca_trade_api as tradeapi
from configmanager import ConfigurationProvider
import logging

class DependencyManager:
    def __init__(self, config_provider: ConfigurationProvider):
        self.config = config_provider.get_config()
        self._token_provider = None
        self._az_openai_client = None
        self._az_openai_reasoning_client = None
        self._az_table_service_client = None
        self._az_table_client = None
        self._az_acs_email_client = None
        self._az_ai_foundry_project_client = None
        self._alpaca_trade_client = None
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing DependencyManager...")

    @property
    def token_provider(self):
        if self._token_provider is None:
            self.logger.info("Initializing token provider...")
            self._token_provider = AzureTokenProvider(   
                DefaultAzureCredential(),  # type: ignore
                self.config.az_cognitive_services_endpoint,
            )
        return self._token_provider
    
    @property
    def az_openai_client(self):
        if self._az_openai_client is None:
            self.logger.info("Initializing Azure OpenAI Chat Completion client...")
            self._az_openai_client = AzureOpenAIChatCompletionClient(
                azure_deployment = self.config.az_openai_model_deployment_name,
                model = self.config.az_openai_model_name,
                api_version = self.config.az_openai_api_version,
                azure_endpoint = self.config.az_openai_endpoint,
                azure_ad_token_provider = self.token_provider,
                temperature=0.5,
            )
        return self._az_openai_client
    
    @property
    def az_openai_reasoning_client(self):
        if self._az_openai_reasoning_client is None:
            self.logger.info("Initializing Azure OpenAI Reasoning client...")
            self._az_openai_reasoning_client = AzureOpenAIChatCompletionClient(
                azure_deployment = self.config.az_openai_reasoning_model_deployment_name,
                model = self.config.az_openai_reasoning_model_name,
                api_version = self.config.az_openai_api_version,
                azure_endpoint = self.config.az_openai_endpoint,
                azure_ad_token_provider = self.token_provider,
            )
        return self._az_openai_reasoning_client
    
    @property
    def az_table_service_client(self):
        if self._az_table_service_client is None:
            self.logger.info("Initializing Azure Table Service client...")
            self._az_table_service_client = TableServiceClient(
                endpoint = self.config.az_storage_table_endpoint,
                credential = ClientSecretCredential(
                    tenant_id = self.config.az_storage_tenant_id,
                    client_id = self.config.az_storage_table_client_id,
                    client_secret = self.config.az_storage_table_client_secret,
                )
            )
        return self._az_table_service_client
    
    @property
    def az_table_client(self):
        if self._az_table_client is None:
            self.logger.info("Initializing Azure Table client...")
            # Ensure the table exists before getting the client.
            self.az_table_service_client.create_table_if_not_exists(
                table_name = self.config.az_storage_table_name,
            )
            
            self.az_table_client = self.az_table_service_client.get_table_client(
                table_name = self.config.az_storage_table_name,
            )
        return self._az_table_client
    
    @az_table_client.setter
    def az_table_client(self, value):
        self._az_table_client = value
    
    @property
    def az_acs_email_client(self):
        if self._az_acs_email_client is None:
            self.logger.info("Initializing Azure Communication Service Email client...")
            connection_string =f"endpoint={self.config.az_comm_service_endpoint};accesskey={self.config.az_comm_service_access_key}"
            self._az_acs_email_client = EmailClient.from_connection_string(connection_string)
        return self._az_acs_email_client
    
    @property
    def alpaca_trade_client(self):
        if self._alpaca_trade_client is None:
            self.logger.info("Initializing Alpaca Trade API client...")
            self._alpaca_trade_client = tradeapi.REST(
                key_id = self.config.alpaca_api_key,
                secret_key = self.config.alpaca_secret_key,
                base_url = self.config.alpaca_paper_trading_base_url,
                api_version = 'v2',
            )
        return self._alpaca_trade_client
    
    @property
    def az_ai_foundry_project_client(self):
        if self._az_ai_foundry_project_client is None:
            self.logger.info("Initializing Azure AI Foundry Project client...")
            self._az_ai_foundry_project_client = AIProjectClient.from_connection_string(
                conn_str = self.config.az_ai_foundry_proj_conn,
                credential = DefaultAzureCredential(),
            )
        return self._az_ai_foundry_project_client
      