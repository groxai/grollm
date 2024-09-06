import os
from dotenv import load_dotenv

import openai
from openai import OpenAIError, AuthenticationError

from .base import LLM_Base

from .cost_manager import CostStore

from .logger import get_logger

load_dotenv()

LOGGER = get_logger(__name__)

pricing_details = {
    "gpt-4o": {
        "prompt_tokens": 5.00 / 1000000,
        "completion_tokens": 15.00 / 1000000,
    },
    "gpt-4o-mini": {
        "prompt_tokens": 0.150 / 1_000000,
        "completion_tokens": 0.600 / 1000000,
    },
    "gpt-4-turbo": {
        "prompt_tokens": 10.00 / 1000000,
        "completion_tokens": 30.00 / 1000000,
    },
    "gpt-4": {
        "prompt_tokens": 30.00 / 1000000,
        "completion_tokens": 60.00 / 1000000,
    },
    "gpt-4-32k": {
        "prompt_tokens": 60.00 / 1000000,
        "completion_tokens": 120.00 / 1000000,
    },
    "gpt-3.5-turbo": {
        "prompt_tokens": 0.50 / 1000000,
        "completion_tokens": 1.50 / 1000000,
    },
}

cs = CostStore(pricing_details)

class OpenAI_Grollm(LLM_Base):
    
    def __init__(self, api_key: str = os.getenv('OPENAI_API_KEY'), 
                 db_uri: str = os.getenv('MLFLOW_DB_URI'),
                 experiment_name: str = "LLM_Experiments_OPENAI", model: str = "gpt-3.5-turbo",
                 cost_store: CostStore = cs):
        
        super().__init__(api_key=api_key, db_uri=db_uri, experiment_name=experiment_name)
        self.model = model
        openai.api_key = os.getenv('OPENAI_API_KEY', api_key)
        self.cost_store = cost_store
        self._validate_cost(pricing_details.get(model, {}))

    def _check_api_key_health(self) -> bool:
        try:
            openai.models.list()
            return True
        except AuthenticationError:
            LOGGER.error("Authentication error: Invalid API key.")
            LOGGER.error("Please check your API key and update it in .env file present at the root directory of grollm.")
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
            LOGGER.info("Sending request to OpenAI API.")
            LOGGER.debug(f"Model: {self.model}")
            LOGGER.debug(f"Messages: {messages}")

            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )

            response_text = response.choices[0].message.content
            tokens_used = self.calculate_tokens(**response.usage.to_dict())
            self.add_to_cumulative_tokens(tokens_used)

            LOGGER.info("Received response from OpenAI API.")
            LOGGER.debug(f"Response: {response_text}")
            return response_text

        except OpenAIError as e:
            LOGGER.error(f"An OpenAI API error occurred: {e}")
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
    ol = OpenAI_Grollm()
    if ol.is_available:
        prompt = "What is the meaning of life on earth?"
        response = ol.send_prompt(prompt)
        print(f"Response: {response}")

        prompt = "What is the meaning of life on moon?"
        response = ol.send_prompt(prompt)
        print(f"Response: {response}")

    else:
        print("API key is not valid.")
