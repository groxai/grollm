# grollm
![Jira FStack Logo](./images/9m42vusr.png)

**grollm** is a Python package that simplifies interactions with major Large Language Model (LLM) APIs, including OpenAI, Google Gemini, and Anthropic. It features easy-to-use wrappers and integrates with MLflow for detailed token usage tracking.

## Description

**grollm** is a powerful Python package that provides seamless wrappers for leading LLM APIs. Designed to streamline the development process, `grollm` abstracts the complexities of these APIs, allowing developers to integrate LLM functionalities with minimal effort.

Key features of `grollm` include:

- **Unified API Access**: Simplify your code by using consistent interfaces for different LLM providers.
- **Ease of Use**: Avoid the hassle of learning the specific details of each API. `grollm` handles the intricacies for you.
- **MLflow Integration**: Track and manage your token usage effectively with built-in MLflow support, enabling detailed monitoring of API consumption and cost.

## Installation

You can install `grollm` via pip:

```python
pip install grollm
```

## Getting Started

Create a .env file locally wherever you want to use this package

```python
# api key required to be used respective packages

OPENAI_API_KEY = "<openai-api-key>" #Optional
GEMINI_API_KEY = "<gemini-api-key>" #Optional
ANTHROPIC_API_KEY = "<claude-api-key>" #Optional
MLFLOW_DB_URI = "<mlflow-db-uri>" #Optional, to use ml flow. Leave blank if not required. Ex sqlite:///logs/mlflow.db
```

## Example Usage

Here’s a quick example demonstrating how to use `grollm` with the Google Gemini API:

```python
from dotenv import load_dotenv
load_dotenv()  # Ensure .env file is present in your directory

from grollm import Gemini_Grollm

gl = Gemini_Grollm()
prompt_message = "You are an expert Python developer. Please generate 'hello world' whenever you see a full stop in code."

gl.send_prompt(prompt_message)
```

### Expected Output

Running the above code will produce log output similar to this:

```
2024-11-14 12:05:15 -- INFO -- grollm.gemini_gro -- send_prompt -- (48) -- Sending request to Google Gemini API.
2024-11-14 12:05:15 -- DEBUG -- grollm.gemini_gro -- send_prompt -- (49) -- Model: gemini-1.0-pro-latest
2024-11-14 12:05:15 -- DEBUG -- grollm.gemini_gro -- send_prompt -- (50) -- Messages: You are an expert python developer. Please generate hello world whenever you see a full stop in code
2024-11-14 12:05:17 -- DEBUG -- grollm.gemini_gro -- calculate_tokens -- (73) -- Completion tokens: 10, Prompt tokens: 0, Total tokens: 30
2024-11-14 12:05:17 -- INFO -- grollm.gemini_gro -- send_prompt -- (58) -- Received response from Google Gemini API.
2024-11-14 12:05:17 -- DEBUG -- grollm.gemini_gro -- send_prompt -- (59) -- Response: ```python
print("hello world.")
```

## For building package locally

You can install `hatchling` via pip:

```python
pip install hatchling
hatchling build
```