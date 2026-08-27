import os
from dotenv import load_dotenv, find_dotenv, dotenv_values


env_path = find_dotenv('.env', raise_error_if_not_found=True)
# Load the .env file into a dictionary.
env_config = dotenv_values(env_path)
# Flush (remove) any cached variables in os.environ that are defined in the .env file.
for key in env_config:
    if key in os.environ:
        del os.environ[key]
# Re-load the environment variables from the .env file.
load_dotenv(env_path)

class ConfigurationManager:
    def __init__(self):
        self.az_cognitive_services_endpoint = os.getenv("AZURE_COGNITIVE_SERVICES_ENDPOINT")
        self.az_ai_foundry_proj_conn = os.getenv("AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING")
        self.az_storage_table_endpoint = os.getenv("AZURE_STORAGE_TABLE_ENDPOINT")
        self.az_storage_table_name = os.getenv("AZURE_STORAGE_TABLE_NAME")
        self.az_storage_table_client_id = os.getenv("AZURE_TABLESTORAGE_CLIENT_ID")
        self.az_storage_table_client_secret = os.getenv("AZURE_TABLESTORAGE_CLIENT_SECRET")
        self.az_storage_tenant_id = os.getenv("AZURE_STORAGE_TENANT_ID")
        self.az_comm_service_endpoint = os.getenv("AZURE_COMM_SERVICE_ENDPOINT")
        self.az_comm_service_access_key = os.getenv("AZURE_COMM_SERVICE_ACCESS_KEY")
        self.bing_conn_name = os.getenv("BING_CONNECTION_NAME")
        self.az_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.az_openai_model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
        self.az_openai_model_deployment_name = os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME")
        self.az_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.az_openai_reasoning_model_name = os.getenv("AZURE_OPENAI_REASONING_MODEL_NAME")
        self.az_openai_reasoning_model_deployment_name = os.getenv("AZURE_OPENAI_REASONING_MODEL_DEPLOYMENT_NAME")
        self.alpaca_paper_trading_base_url = os.getenv("ALPACA_PAPER_TRADING_BASE_URL")
        self.alpaca_api_key = os.getenv("ALPACA_API_KEY")
        self.alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.fin_modeling_prep_base_url = os.getenv("FINANCIAL_MODELING_PREP_BASE_URL")
        self.fin_modeling_prep_api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
        self.indianapi_base_url = os.getenv("INDIANAPI_BASE_URL")
        self.indianapi_api_key = os.getenv("INDIANAPI_API_KEY")


class ConfigurationProvider:
    def __init__(self, config_manager: ConfigurationManager):
        self._config = config_manager

    def get_config(self):
        missing_configs = []
        for attr, value in vars(self._config).items():
            if not value:
                # If the value is None or empty, add it to the missing_config list. :
                missing_configs.append(attr)
        
        if missing_configs:
            raise ValueError(f"The following configuration variables are missing or not set: {', '.join(missing_configs)}")
        # If all required configurations are present, return the config object.
        return self._config  