import os
from dotenv import load_dotenv

import openai
from openai import AzureOpenAI, OpenAIError, AuthenticationError

from .base import LLM_Base

from .cost_manager import CostStore

from .logger import get_logger

load_dotenv()

LOGGER = get_logger(__name__)

pricing_details = {
    "gpt-4-turbo-2024-04-09": {
        "prompt_tokens": 10.00 / 1000000,
        "completion_tokens": 30.00 / 1000000,
    }
}

AZUREOPENAI_DEPLOYMENT_NAME = "gpt-4-turbo-2024-04-09"

cs = CostStore(pricing_details)

class AzureOpenAI_Grollm(LLM_Base):

    def __init__(self, 
                 api_key: str = os.getenv('AZUREOPENAI_API_KEY'), 
                 api_version : str = os.getenv('AZUREOPENAI_API_VERSION'),
                 db_uri: str = os.getenv('MLFLOW_DB_URI'), 
                 mlflow_flag: bool = False, 
                 experiment_name: str = "LLM_Experiments_AZURE_OPENAI", 
                 model: str = AZUREOPENAI_DEPLOYMENT_NAME, 
                 deployment_name: str = AZUREOPENAI_DEPLOYMENT_NAME,
                 endpoint: str = os.getenv('AZUREOPENAI_ENDPOINT'),
                 cost_store: CostStore = cs):
        
        super().__init__(api_key=api_key, db_uri=db_uri, mlflow_flag=mlflow_flag, experiment_name=experiment_name)
        self.api_version = api_version
        self.model = model
        self.deployment_name = deployment_name
        self.endpoint = endpoint
        self.cost_store = cost_store
        
        if not all([self.api_key, self.deployment_name, self.endpoint]):
            raise ValueError("Azure OpenAI API key, deployment name, and endpoint must be provided.")
        
        # Configure OpenAI with Azure-specific settings
        openai.api_type = "azure"
        openai.api_key = self.api_key
        openai.api_base = self.endpoint
        openai.api_version = self.api_version

        # Configure Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=self.api_version
        )

        self._validate_cost(pricing_details.get(model, {}))

    def _check_api_key_health(self) -> bool:
        """
        Checks the health of the Azure OpenAI API key without consuming tokens by listing available deployments.
        """
        try:
            # Use the Azure OpenAI client to list deployments
            deployments = self.client.models.list()  # Fetch available models/deployments
            
            import pdb
            pdb.set_trace()
            
            if self.deployment_name in [deployment.id for deployment in deployments.data]:
                LOGGER.info(f"Deployment '{self.deployment_name}' is available.")
                return True
            else:
                LOGGER.error(f"Deployment '{self.deployment_name}' not found.")
                return False

        except AuthenticationError:
            LOGGER.error("Authentication error: Invalid Azure OpenAI API key or configuration.")
            return False
        except OpenAIError as e:
            LOGGER.error(f"An error occurred while checking API key health: {e}")
            return False

    def send_prompt(self, prompt, **kwargs) -> str:
        if isinstance(prompt, str):
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        elif isinstance(prompt, list) and all(isinstance(m, dict) for m in prompt):
            messages = prompt
        else:
            raise ValueError("Prompt must be a string or a list of message dictionaries.")

        try:
            LOGGER.info("Sending request to Azure OpenAI API.")
            LOGGER.debug(f"Model: {self.model}")
            LOGGER.debug(f"Messages: {messages}")

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                **kwargs
            )

            response_text = response.choices[0].message.content
            tokens_used = self.calculate_tokens(**response.usage.to_dict())
            self.add_to_cumulative_tokens(tokens_used)

            LOGGER.info("Received response from Azure OpenAI API.")
            LOGGER.debug(f"Response: {response_text}")
            return response_text

        except OpenAIError as e:
            LOGGER.error(f"An Azure OpenAI API error occurred: {e}")
            raise

    @LLM_Base.add_to_cumulative_tokens
    def calculate_tokens(self, *args, **kwargs) -> int:
        completion_tokens = kwargs.get('completion_tokens', 0)
        prompt_tokens = kwargs.get('prompt_tokens', 0)
        total_tokens = kwargs.get('total_tokens', 0)

        LOGGER.debug(f"Completion tokens: {completion_tokens}, Prompt tokens: {prompt_tokens}, Total tokens: {total_tokens}")
        return kwargs

    def set_token_cost(self, cost_per_token: float):
        cost_per_token = self._validate_cost(cost_per_token)
        super().set_token_cost(cost_per_token)


if __name__ == "__main__":
    azure_ol = AzureOpenAI_Grollm()
    if azure_ol.is_available:
        prompt = "What is the meaning of life on earth?"
        response = azure_ol.send_prompt(prompt)
        print(f"Response: {response}")

        prompt = "What is the meaning of life on moon?"
        response = azure_ol.send_prompt(prompt)
        print(f"Response: {response}")
    else:
        print("Azure OpenAI API key or configuration is not valid.")
