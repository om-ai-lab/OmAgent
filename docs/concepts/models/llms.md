# LLMs
LLMs are the core components of Omagent. They are responsible for generating text via Large Language Models.

It is constructed by following parts:
- ```BaseLLM```: The base class for all LLMs, it defines the basic properties and methods for all LLMs.
- ```BaseLLMBackend```: The enhanced class for better using LLMs, you can assemble specific LLMs with different prompt templates and output parsers.
- ```BasePromptTemplate```: The base class for all prompt templates, it defines the input variables and output parser for a prompt template.
- ```BaseOutputParser```: The base class for all output parsers, it defines how to parse the output of an LLM result.

## Prompt Template
This is a simple way to define a prompt template.
```python
from omagent_core.models.llms.prompt.prompt import PromptTemplate

# Define a system prompt template
system_prompt = PromptTemplate.from_template("You are a helpful assistant.", role="system")
# Define a user prompt template
user_prompt = PromptTemplate.from_template("Tell me a joke about {{topic}}", role="user")
```
`topic` is a variable in the user prompt template, it will be replaced by the actual input value.

## Output Parser
This is a simple way to define a output parser.
```python
from omagent_core.models.llms.prompt.parser import StrParser

output_parser = StrParser()
```
`StrParser` is a simple output parser that returns the output as a string.

## Get LLM Result
This is a simple way to define a LLM request and get the result of an LLM.
1. The worker class should inherit from `BaseWorker` and `BaseLLMBackend`, and define the LLM model in the `prompts` and `llm` field. `OutputParser` is optional, if not defined, the default `StrParser` will be used.
2. Override the `_run` method to define the workflow logic.
```python
def _run(self, *args, **kwargs):
    payload = {
        "topic": "weather"
    }
    # 1. use the `infer` method to get the LLM result
    chat_complete_res = self.infer(input_list=[payload])[0]["choices"][0]["message"].get("content")
    # 2. use the `simple_infer` method to get the LLM result, it's a shortcut for the `infer` method
    simple_infer_res = self.simple_infer(topic="weather")["choices"][0]["message"].get("content")
    content = chat_complete_res[0]["choices"][0]["message"].get("content")
    print(content)
    return {'output': content}
```

For Multi-Modal LLMs, it's also simple and intuitive.
```python
def _run(self, *args, **kwargs):
    payload = {
        "topic": ["this image", PIL.Image.Image object, ...]
    }
    chat_complete_res = self.infer(input_list=[payload])[0]["choices"][0]["message"].get("content")
    return {'output': chat_complete_res}
```
The order of prompts given to the LLM is consistent with the order of elements in the list of variables, resulting in an alternating pattern of text and images.