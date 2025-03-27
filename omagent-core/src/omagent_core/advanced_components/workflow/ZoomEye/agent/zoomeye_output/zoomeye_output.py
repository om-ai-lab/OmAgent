from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.advanced_components.workflow.ZoomEye.schemas.utils import *

@registry.register_worker()
class ZoomEyeOutput(BaseWorker, BaseLLMBackend):
    """
    Worker class responsible for generating the final response to the user's query.
    Combines the search results with the original query and image to create a comprehensive answer.
    """

    llm: OpenaiGPTLLM  # Language model used for generating the final output

    def _run(self, *args, **kwargs):
        """
        Main execution method to generate the final response based on search results.
        
        Args:
            *args: Variable length argument list (not used)
            **kwargs: Arbitrary keyword arguments (not used)
            
        Returns:
            dict: Contains the final result with the answer, query information, and token usage statistics
        """
        # Retrieve the final set of candidates (search results) from short-term memory
        final_all_candidates = self.stm(self.workflow_instance_id)['final_all_candidates']
        
        # Get the original image from the cache
        image_pil = self.stm(self.workflow_instance_id)['image_cache']['<image_0>']
        
        # Get the user's original question
        question = self.stm(self.workflow_instance_id)['prompt']
            
        # Create a conversation prompt that includes the search results, image, and original question
        conversation = get_output_conversation(final_all_candidates, image_pil, question)
        
        # Generate the final answer using the language model
        response = self.llm.generate(conversation)
        
        # Track token usage for monitoring and billing purposes
        prompt_tokens = self.stm(self.workflow_instance_id).get('prompt_tokens', 0)
        completion_tokens = self.stm(self.workflow_instance_id).get('completion_tokens', 0)
        self.stm(self.workflow_instance_id)['prompt_tokens'] = prompt_tokens + response['usage']['prompt_tokens']
        self.stm(self.workflow_instance_id)['completion_tokens'] = completion_tokens + response['usage']['completion_tokens']
        
        # Extract the content of the LLM's response
        res = response['choices'][0]['message']['content']
        
        # Log the final output for monitoring
        self.callback.info(self.workflow_instance_id, progress='ZoomEyeOutput', message=f'\nZoomEyeOutput: {res}')
        
        # Compile the complete result package with query information and usage statistics
        result = {
            "id": self.stm(self.workflow_instance_id).get('id', None),   # Query identifier
            "query": self.stm(self.workflow_instance_id).get('prompt', None),  # Original user query
            "last_output": res,  # Final answer text
            "prompt_tokens": self.stm(self.workflow_instance_id)['prompt_tokens'],  # Total prompt tokens used
            "completion_tokens": self.stm(self.workflow_instance_id)['completion_tokens'],  # Total completion tokens used
        }
        
        # Return the final result to be presented to the user
        return {"result": result}
        