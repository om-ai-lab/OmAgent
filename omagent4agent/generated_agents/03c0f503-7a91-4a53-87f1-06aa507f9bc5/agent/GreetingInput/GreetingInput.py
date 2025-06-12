
from omagent_core.omagent4agent import *

@registry.register_worker()
class GreetingInput(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(default=[])

    def _run(self, input, *args, **kwargs):
        # Validate input exists and is not empty
        if not input:
            raise ValueError("Greeting input cannot be empty")
        
        # Store input in short-term memory
        self.stm(self.workflow_instance_id)["greeting_input"] = input
        print(f"Stored greeting input in short-term memory: {input}")
