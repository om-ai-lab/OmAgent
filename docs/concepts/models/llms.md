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

You can refer to the [image chat example](https://github.com/om-ai-lab/OmAgent/tree/main/examples/image_chat) to see how to use LLMs.