import os
from dotenv import load_dotenv

import google.generativeai as gemini  # Assuming a similar library or use the appropriate one

from .base import LLM_Base

from .cost_manager import CostStore

from .logger import get_logger

load_dotenv()

LOGGER = get_logger(__name__)

pricing_details= {}

cs = CostStore(pricing_details)

class Gemini_Grollm(LLM_Base):
    
    def __init__(self, api_key: str = os.getenv('GEMINI_API_KEY'), 
                 db_uri: str = os.getenv('MLFLOW_DB_URI'),
                 mlflow_flag: bool = False,
                 experiment_name: str = "LLM_Experiments_GEMINI", 
                 model: str = 'gemini-1.0-pro-latest',
                 cost_store: CostStore = cs):
        
        super().__init__(api_key=api_key, db_uri=db_uri, mlflow_flag=mlflow_flag, experiment_name=experiment_name)
        gemini.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = model
        self.gemini_client = gemini.GenerativeModel(self.model)
        self.cost_store = cost_store
        self._validate_cost(pricing_details.get(model, {}))
        
    def _check_api_key_health(self):
        try:
            # Make a basic request to check API health
            self.gemini_client.generate_content("Hello, world!")
            return True
        except Exception as e:
            LOGGER.error(f"API key health check failed: {e}")
            return False

    def send_prompt(self, prompt, **kwargs) -> str:

        if isinstance(prompt, str):
            try:
                LOGGER.info("Sending request to Google Gemini API.")
                LOGGER.debug(f"Model: {self.model}")
                LOGGER.debug(f"Messages: {prompt}")

                response = self.gemini_client.generate_content(prompt)
                response_text = response.text

                tokens_used = self.calculate_tokens(**response.to_dict()['usage_metadata'])
                self.add_to_cumulative_tokens(tokens_used)

                LOGGER.info("Received response from Google Gemini API.")
                LOGGER.debug(f"Response: {response_text}")
            except Exception as e:
                LOGGER.error(f"An Google Gemini API error occurred: {e}")
                raise
        else:
            raise ValueError("Prompt must be a string")
        
    @LLM_Base.add_to_cumulative_tokens
    def calculate_tokens(self, *args, **kwargs) -> int:

        completion_tokens = kwargs.get('candidates_token_count', 0)
        prompt_tokens = kwargs.get('prompt_tokens', 0)
        total_tokens = kwargs.get('total_token_count', 0)

        LOGGER.debug(f"Completion tokens: {completion_tokens}, Prompt tokens: {prompt_tokens}, Total tokens: {total_tokens}")
        return kwargs

    def set_token_cost(self, cost_per_token: float):
        cost_per_token = self._validate_cost(cost_per_token)
        super().set_token_cost(cost_per_token)

if __name__ == "__main__":

    gemini_client = Gemini_Grollm()

    if gemini_client.is_available:
        prompt = "What is the meaning of life on sun?"
        response = gemini_client.send_prompt(prompt)
        print(f"Response: {response}")

        prompt = "What is the meaning of life on moon?"
        response = gemini_client.send_prompt(prompt)
        print(f"Response: {response}")

    else:
        print("API key is not valid.")
