import pip
from collections import Counter

def import_or_install(package = "mlflow"):

    try:
        return __import__(package)
    
    except ImportError:
        if package == "mlflow":
            pip.main(['install', 'mlflow==2.15.1'])
        else:
            pip.main(['install', package])
        
        return __import__(package)
        
def multiply_counters(counter1: Counter, counter2: Counter) -> Counter:

    common_keys = counter1.keys() & counter2.keys()
    result = Counter()
    for key in common_keys:
        result[key] = counter1[key] * counter2[key]
    return result

def add_counters(dict1, dict2):
    merged = Counter(dict1)  # Start with dict1 as the base
    for key, value in dict2.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # If both values are dictionaries, merge them recursively
            merged[key] = add_counters(merged[key], value)
        else:
            # Otherwise, sum the values (or simply assign if non-numeric)
            merged[key] += value if isinstance(value, (int, float)) else value
    return merged