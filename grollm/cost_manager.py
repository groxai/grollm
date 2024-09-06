import warnings

from pydantic import BaseModel

class CostModel(BaseModel):
    name: str
    cost_dict: dict = {}

class CostStore:

    def __init__(self, pricing_dict: dict = {}) -> None:
        self.pricing_dict = pricing_dict
        self._validate_pricing_dict()
        
    def _validate_pricing_dict(self):
        for model, cost_dict in self.pricing_dict.items():
            if not isinstance(model, str):
                raise ValueError("Model name must be a string.")
            if not isinstance(cost_dict, dict):
                raise ValueError("Cost dictionary must be a dictionary.")
            if not all(isinstance(value, float) for value in cost_dict.values()):
                raise ValueError("Cost values must be floats.")

    def get_model_pricing(self, model: str) -> CostModel:
        
        if model not in self.pricing_dict:
            warnings.warn(f"Model {model} not found in pricing dictionary, setting prices as empty")
            return CostModel(name=model, cost_dict={})
        
        return CostModel(name=model, cost_dict=self.pricing_dict[model])