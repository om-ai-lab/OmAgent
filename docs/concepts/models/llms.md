# LLMs
LLMs are the core components of Omagent. They are responsible for generating text via Large Language Models.

It is constructed by following parts:
- ```BaseLLM```: The base class for all LLMs, it defines the basic properties and methods for all LLMs.
- ```BasePromptTemplate```: The base class for all prompt templates, it defines the prompt framework, input variables for a prompt template.
- ```BaseOutputParser```: The base class for all output parsers, it defines how to parse the output of the LLM result.
- ```BaseLLMBackend```: The enhanced class for better using LLMs, you can assemble specific LLMs with different prompt templates and output parsers. It provides an elegant way to use LLMs.

## BaseLLM
BaseLLM is a base class for defining a LLM, providing basic attributes, parameters and calling methods. All LLM models should inherit from BaseLLM.

### Define a custom LLM
```python
from omagent_core.models.llms.base import BaseLLM
from omagent_core.utils.registry import registry


@registry.register_llm()
class CustomLLM(BaseLLM):
    # necessary attributes
    model_id: str = Field(default="custom_llm", description="The model id of custom llm")
    api_key: str = Field(default="custom_api_key", description="The api key of custom llm")
    endpoint: str = Field(default="custom_endpoint", description="The endpoint of custom llm")

    def model_post_init(self, __context: Any) -> None:
        # init your llm client here
        pass
    def _call(self, records: List[Message], **kwargs) -> str:
        # synchronous call function
        # implement your llm sync call logic here
        pass
    async def _acall(self, records: List[Message], **kwargs) -> str:
        # asynchronous call function
        # implement your llm async call logic here
        pass
```
For a complete example, you can refer to the [OpenaiGPTLLM](https://github.com/om-ai-lab/OmAgent/blob/main/omagent-core/src/omagent_core/models/llms/openai_gpt.py) implementation.

## Prompt Template
Prompt template is used to define the prompt framework for requesting LLM, supporting variable definition through `{{variable}}` in the prompt, which will be replaced with actual input values at runtime.
### How to use Prompt Template
1. PromptTemplate.from_template(): Define prompt template from a string.
   ```python
    # Define a system prompt template
    system_prompt = PromptTemplate.from_template("You are a helpful assistant.", role="system")
    # Define a user prompt template
    user_prompt = PromptTemplate.from_template("Tell me a joke about {{topic}}", role="user")
   ```
   `topic` is a variable in the user prompt template, it will be replaced by the actual input value.
2. PromptTemplate.from_file(): Define prompt template from a file.
    ```python
    from omagent_core.models.llms.prompt.prompt import PromptTemplate

    # Define a system prompt template
    # content in path-to-system-prompt-file: You are a helpful assistant.
    system_prompt = PromptTemplate.from_file("path-to-system-prompt-file", role="system")
    # Define a user prompt template
    # content in path-to-user-prompt-file: Tell me a joke about {{topic}} in {{language}}
    user_prompt = PromptTemplate.from_file("path-to-user-prompt-file", role="user")
    ```
    `topic` and `language` are variables in the user prompt template, they will be replaced by the actual input value.
### Understand Prompt Template
Prompt Template is designed to be a user-friendly component, where users only need to define variable names and provide variable values, and OmAgent will automatically assemble variables.
#### Supported variable value types
Prompt Template supports the following **variable** value types:
1. `string`: string.
2. `list`: List, when sending to LLM, the data in the list except for `PIL.Image.Image` will be automatically converted to string.
3. `dict`: Dictionary, when sending to LLM, the data in the dictionary except for `PIL.Image.Image` will be automatically converted to string.
4. `PIL.Image.Image`: Image, when sending to LLM, the image will be automatically converted to base64.

#### Variable assembly rules
Prompt Template variable assembly follows the variable order defined in the template, replacing each variable with the corresponding variable value. 
If the variable value is of type `list` or `dict`, and there is image data, the image will be automatically replaced with its base64 encoding, and the image and text will be automatically combined into a mixed data structure.

## Output Parser
Output parser is used to parse the output of an LLM, supporting the following output parsers:
1. `StrParser`: String parser, returns the output of the LLM as a string.
2. `DictParser`: Dictionary parser, returns the output of the LLM as a python dictionary.
3. `ListParser`: List parser, returns the output of the LLM as a python list.

### How to use
```python
from omagent_core.models.llms.prompt.parser import StrParser

output_parser = StrParser()
parsed_output = output_parser.parse(llm_output)
```

## BaseLLMBackend
BaseLLMBackend is the class that actually calls the LLM. It aggregates the corresponding LLM, Prompt Template and Output Parser, which can be easily defined through configuration files and provides some convenient methods to call LLM, such as `simple_infer` and `infer`.
You can quickly call LLM through BaseLLMBackend using the following configuration file:

```yaml
name: OpenaiGPTLLM # which LLM class you want to use, OpenaiGPTLLM is based on BaseLLM, implementing how to call Openai's LLM
model_id: gpt-4o # model id
api_key: ${env| custom_openai_key, null} # API key, gets the API key from environment variable {custom_openai_key}, defaults to null if not found
endpoint: ${env| custom_openai_endpoint, https://api.openai.com/v1} # endpoint, gets the endpoint from environment variable {custom_openai_endpoint}, defaults to https://api.openai.com/v1 if not found
temperature: 0 # model temperature
vision: true # Whether the large model supports vision
response_format: json_object # Large model output format
use_default_sys_prompt: true # Whether to use default system prompt, including current time, region, operating system and other information
```


## Get LLM Result
This is a simple way to define a LLM request and get the result of an LLM.
```python
from typing import List
from pydantic import Field
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.models.llms.prompt.parser import *
from PIL import Image

class LLMTest(BaseLLMBackend):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template("You are a helpful assistant.", role="system"),
            PromptTemplate.from_template("describe the {{image}} in {{language}}", role="user"),
        ]
    )
    llm: OpenaiGPTLLM ={
        "name": "OpenaiGPTLLM", 
        "model_id": "gpt-4o", 
        "api_key": "Your openai api key", 
        "vision": True
        }
    output_parser: StrParser = StrParser()

llm_test = LLMTest()
img = Image.open("OmAgent/docs/images/app_album_img.png")

# 1. use the `infer` method to get the LLM result
res = llm_test.infer(input_list=[{"image": img, "language": "english"}])[0]["choices"][0]["message"].get("content")
print(llm_test.output_parser.parse(res))
# the value of variable can be a mixture of string, list, dict and PIL.Image.Image
res1 = llm_test.infer(input_list=[{"image": [img, "with a poem"], "language": ["english", "chinese"]}])[0]["choices"][0]["message"].get("content")
print(llm_test.output_parser.parse(res1))

# 2. use the `simple_infer` method to get the LLM result, it's a shortcut for the `infer` method
simple_infer_res = llm_test.simple_infer(image=img)["choices"][0]["message"].get("content")
print(llm_test.output_parser.parse(simple_infer_res))

```


For detailed examples, you can refer to the [image chat example](https://github.com/om-ai-lab/OmAgent/tree/main/examples/image_chat).
