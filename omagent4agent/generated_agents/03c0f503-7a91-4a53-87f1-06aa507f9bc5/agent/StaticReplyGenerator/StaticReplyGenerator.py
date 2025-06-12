from omagent_core.omagent4agent import *

@registry.register_worker()
class StaticReplyGenerator(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(default=[])

    def _run(self, *args, **kwargs):
        # Generate static response
        static_response = "hi"
        
        # Store response in short-term memory
        self.stm(self.workflow_instance_id)["static_response"] = static_response
        print(f"Stored static reply in short-term memory: {static_response}")

        # Final worker returns output according to documentation
        return {"last_output": static_response}
