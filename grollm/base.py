from abc import ABC, abstractmethod
from functools import wraps
from collections import Counter
import uuid

def multiply_counters(counter1: Counter, counter2: Counter) -> Counter:

    common_keys = counter1.keys() & counter2.keys()
    result = Counter()
    for key in common_keys:
        result[key] = counter1[key] * counter2[key]
    return result

class LLM_Base(ABC):

    def __init__(self, api_key: str, db_uri: str, experiment_name: str):
        self.api_key = api_key
        self.cumulative_tokens = Counter()
        self.cumulative_cost = Counter()

        if db_uri is not None:
            import mlflow
            self._initialize_mlflow(db_uri=db_uri, experiment_name=experiment_name)

    def _validate_cost(self, cost_dict: dict):

        if cost_dict is not None:
            for item,value in cost_dict.items():
                if value < 0:
                    raise ValueError(f"{item} cost must be non-negative.")
                
            self.cost_dict = Counter(cost_dict)
        else:
            self.cost_dict = Counter({})   

    @abstractmethod
    def _check_api_key_health(self):
        pass
    
    @property
    def is_available(self) -> bool:
        return self._check_api_key_health()

    @abstractmethod
    def send_prompt(self, *args, **kwargs):
        pass
    
    @staticmethod
    def add_to_cumulative_tokens(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            tokens_used = func(*args, **kwargs)
            if isinstance(tokens_used, dict):
                self.cumulative_tokens += Counter(tokens_used)
            else:
                self.cumulative_tokens['total'] += tokens_used
            
            if self.db_uri is not None:
                self._log_to_mlflow(tokens_used)
                self._log_to_mlflow(self.tokens_session_cost)
            return tokens_used
        return wrapper
    
    def _validate_api_key(self, class_name: str):
    
        if self.api_key is None:
            user_api_key = input("Please enter your API key: ")

            if user_api_key is None:
                raise ValueError("API key is required to run this package.")
            else:
                self.api_key = user_api_key

                with open(".env", "a") as f:
                    f.write(f"{class_name}_API_KEY={user_api_key}\n")
                    print(".env file created at the root directory with API key.")
                    print(".env file updated with API key.")

    @abstractmethod
    def calculate_tokens(self, *args, **kwargs) -> dict:
        pass

    @property
    def tokens_used(self):
        return dict(self.cumulative_tokens)
    
    @property
    def set_token_cost(self, cost_dict: dict):
        self._validate_cost(cost_dict)
        self.cost_dict = cost_dict

    @property
    def tokens_session_cost(self):
        self.cumulative_cost += multiply_counters(self.cost_dict, self.cumulative_tokens)
        adjusted_cost_dict = {}
        for key, value in self.cumulative_cost.items():
            adjusted_cost_dict[f"{key}_cost"] = value

        return adjusted_cost_dict

    def _initialize_mlflow(self, db_uri, experiment_name = "LLM_Experiments"):

        mlflow.set_tracking_uri(db_uri)
        mlflow.set_experiment(experiment_name)
        self._current_run_id = mlflow.start_run().info.run_id

    def _log_to_mlflow(self, details: dict):

        with mlflow.start_run(run_id=self._current_run_id, nested=True):
            for key, value in details.items():
                mlflow.log_metric(key, value)