# MiniMax

[MiniMax](https://www.minimax.io/) provides large language models accessible via an OpenAI-compatible API. OmAgent supports MiniMax as a first-class LLM provider through the `MiniMaxLLM` class.

## Supported Models

| Model | Context Window | Description |
|-------|---------------|-------------|
| MiniMax-M3 | 1M tokens | Current flagship model |
| MiniMax-M2.7 | 1M tokens | Earlier flagship model |
| MiniMax-M2.7-highspeed | 1M tokens | High-speed variant of M2.7 |
| MiniMax-M2.5 | 204K tokens | Previous generation model |
| MiniMax-M2.5-highspeed | 204K tokens | High-speed variant of M2.5 |

## Setup

1. Get your API key from [MiniMax Platform](https://platform.minimax.chat/).
2. Set the environment variable:
   ```bash
   export MINIMAX_API_KEY="your_minimax_api_key"
   ```

## Configuration

### YAML Configuration

Create a YAML config file (e.g., `configs/llms/minimax.yml`):

```yaml
name: MiniMaxLLM
model_id: MiniMax-M3
api_key: ${env| MINIMAX_API_KEY}
endpoint: https://api.minimax.io/v1
temperature: 0
```

### Python Configuration

```python
from omagent_core.models.llms.minimax_llm import MiniMaxLLM

llm = MiniMaxLLM(
    model_id="MiniMax-M3",
    api_key="your_api_key",
    temperature=0,
)
```

### Using with BaseLLMBackend

```python
from typing import List
from pydantic import Field
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.minimax_llm import MiniMaxLLM
from omagent_core.models.llms.prompt.prompt import PromptTemplate
from omagent_core.models.llms.prompt.parser import StrParser

class MyAgent(BaseLLMBackend):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template("You are a helpful assistant.", role="system"),
            PromptTemplate.from_template("{{instruction}}", role="user"),
        ]
    )
    llm: MiniMaxLLM = {
        "name": "MiniMaxLLM",
        "model_id": "MiniMax-M3",
        "api_key": "your_api_key",
    }
    output_parser: StrParser = StrParser()
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_id` | str | `MiniMax-M3` | The model to use |
| `api_key` | str | `$MINIMAX_API_KEY` | Your MiniMax API key |
| `endpoint` | str | `https://api.minimax.io/v1` | API endpoint URL |
| `temperature` | float | `0.7` | Sampling temperature (0-1.0) |
| `top_p` | float | `1.0` | Top-p sampling parameter |
| `max_tokens` | int | `2048` | Maximum tokens to generate |
| `stream` | bool | `false` | Enable streaming responses |
| `response_format` | str | `text` | Response format (`text` or `json_object`) |

## Notes

- Temperature is automatically clamped to the [0, 1.0] range.
- The MiniMax API is OpenAI-compatible, so it works seamlessly with the OpenAI SDK.
- Think tags (`<think>...</think>`) in model responses are automatically stripped.
