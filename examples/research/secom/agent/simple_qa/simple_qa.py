import json
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.logger import logging

CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class SimpleQA(BaseWorker, BaseLLMBackend):
    """Simple QA processor that answers questions and segments conversation history by topic."""

    def _run(self, user_instruction: str, *args, **kwargs):
        # Check for termination condition
        if user_instruction.strip().lower() == "bye":
            return {"terminate": True}

        # Retrieve conversation history
        conversation_history = self.stm(self.workflow_instance_id).get("conversation_history", [])

        # Generate a response using LLM
        response = self._generate_response(user_instruction)

        # Save response to conversation history
        conversation_history.append({"role": "bot", "content": response})
        self.stm(self.workflow_instance_id)["conversation_history"] = conversation_history

        # Segment conversation history into topics
        segmented_history = self._segment_conversation(conversation_history)
        self.stm(self.workflow_instance_id)["segmented_history"] = segmented_history

        logging.info(f"Segmented History: {segmented_history}")
        return {"response": response, "terminate": False}

    def _generate_response(self, instruction):
        """Generate a response using the LLM."""
        chat_message = [{"role": "user", "content": instruction}]
        chat_complete_res = self.llm.generate(records=chat_message)
        return chat_complete_res["choices"][0]["message"]["content"]

    def _segment_conversation(self, history):
        """Segment conversation history by topic."""
        prompt = (
            "Segment the following conversation history into topical units. Provide JSON output with "
            "each segment's start, end, and topic description:\n\n"
            f"{json.dumps(history, indent=2)}"
        )
        chat_message = [{"role": "user", "content": prompt}]
        chat_complete_res = self.llm.generate(records=chat_message)
        return json.loads(chat_complete_res["choices"][0]["message"]["content"])

