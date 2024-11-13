import os
from dotenv import load_dotenv

import anthropic
from anthropic import AnthropicError, AuthenticationError

from .base import LLM_Base

from .cost_manager import CostStore

from .logger import get_logger

load_dotenv()

LOGGER = get_logger(__name__)

pricing_details = {
    "claude-2.0": {
        "prompt_tokens": 8.00 / 1000000,
        "completion_tokens": 24.00 / 1000000,
    },
    "claude-2.1": {
        "prompt_tokens": 8.00 / 1000000,
        "completion_tokens": 24.00 / 1000000,
    },
    "claude-instant-1.2": {
        "prompt_tokens": 8.00 / 1000000,
        "completion_tokens": 2.400 / 1000000,
    },
    "claude-3-5-sonnet-20240620": {
        "prompt_tokens": 3.00 / 1000000,
        "completion_tokens": 15.00 / 1000000,
    },
    "claude-3-opus-20240229": {
        "prompt_tokens": 15.00 / 1000000,
        "completion_tokens": 75.00 / 1000000,
    },
    "claude-3-sonnet-20240229": {
        "prompt_tokens": 3.00 / 1000000,
        "completion_tokens": 15.00 / 1000000,
    },
    "claude-3-haiku-20240307": {
        "prompt_tokens": 0.25 / 1000000,
        "completion_tokens": 1.25 / 1000000,
    }
    }

cs = CostStore(pricing_details)

class Anthropic_Grollm(LLM_Base):
    
    def __init__(self, api_key: str = os.getenv('ANTHROPIC_API_KEY'), 
                 db_uri: str = os.getenv('MLFLOW_DB_URI'),
                 mlflow_flag: bool = False,
                 experiment_name: str = "LLM_Experiments_ANTHROPIC", 
                 model: str = "claude-2.1",
                 cost_store: CostStore = cs):
        
        super().__init__(api_key=api_key, db_uri=db_uri, mlflow_flag=mlflow_flag, experiment_name=experiment_name)
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        self.cost_store = cost_store
        self._validate_cost(pricing_details.get(model, {}))
        
    def _check_api_key_health(self) -> bool:
        try:
            # Use the correct prompt format for Anthropic
            self.client.completions.create(
                model=self.model,
                max_tokens_to_sample=128,
                prompt="\n\nHuman: Test.\n\nAssistant:"
            )
            return True
        except AuthenticationError:
            LOGGER.error("Authentication error: Invalid API key.")
            return False
        except AnthropicError as e:
            LOGGER.error(f"An error occurred while checking API key health: {e}")
            return False

    def send_prompt(self, prompt, max_token: int = 1024, **kwargs) -> str:
        if isinstance(prompt, str):
            messages = [
                {"role": "user", "content": prompt}
            ]
        elif isinstance(prompt, list) and all(isinstance(m, dict) for m in prompt):
            messages = prompt
        else:
            raise ValueError("Prompt must be a string or a list of message dictionaries.")

        try:
            LOGGER.info("Sending request to Anthropic API.")
            LOGGER.debug(f"Model: {self.model}")
            LOGGER.debug(f"Messages: {messages}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_token,
                messages=messages,
                **kwargs
            )

            response_text = response.content[0].text
            tokens_used = self.calculate_tokens(prompt_tokens=response.usage.input_tokens, 
                                                completion_tokens=response.usage.output_tokens)
            self.add_to_cumulative_tokens(tokens_used)

            LOGGER.info("Received response from Anthropic API.")
            LOGGER.debug(f"Response: {response_text}")
            return response_text

        except AnthropicError as e:
            LOGGER.error(f"An Anthropic API error occurred: {e}")
            raise
    
    @LLM_Base.add_to_cumulative_tokens
    def calculate_tokens(self, *args, **kwargs) -> int:

        prompt_tokens = kwargs.get('prompt_tokens', 0)
        completion_tokens = kwargs.get('completion_tokens', 0)
        total_tokens = prompt_tokens + completion_tokens

        LOGGER.debug(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total tokens: {total_tokens}")
        return {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens
        }

    def set_token_cost(self, cost_per_token: float):
        cost_per_token = self._validate_cost(cost_per_token)
        self.cost_per_token = cost_per_token

if __name__ == "__main__":
    al = Anthropic_Grollm()
    if al.is_available:
        prompt = "What is the meaning of life on earth?"
        response = al.send_prompt(prompt)
        print(f"Response: {response}")

        prompt = "What is the meaning of life on moon?"
        response = al.send_prompt(prompt)
        print(f"Response: {response}")

    else:
        print("API key is not valid.")