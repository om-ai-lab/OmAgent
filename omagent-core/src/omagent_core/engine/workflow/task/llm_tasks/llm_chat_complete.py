from typing import List, Optional

from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class ChatMessage:

    def __init__(self, role: str, message: str) -> None:
        self.role = role
        self.message = message


class LlmChatComplete(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        llm_provider: str,
        model: str,
        messages: List[ChatMessage],
        stop_words: Optional[List[str]] = [],
        max_tokens: Optional[int] = 100,
        temperature: int = 0,
        top_p: int = 1,
        instructions_template: str = None,
        template_variables: dict[str, object] = {},
    ) -> Self:
        optional_input_params = {}

        if stop_words:
            optional_input_params.update({"stopWords": stop_words})

        if max_tokens:
            optional_input_params.update({"maxTokens": max_tokens})

        input_params = {
            "llmProvider": llm_provider,
            "model": model,
            "promptVariables": template_variables,
            "temperature": temperature,
            "topP": top_p,
            "instructions": instructions_template,
            "messages": messages,
        }

        input_params.update(optional_input_params)

        super().__init__(
            task_name="llm_chat_complete",
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_CHAT_COMPLETE,
            input_parameters=input_params,
        )

    def prompt_variables(self, variables: dict[str, object]) -> Self:
        self.input_parameters["promptVariables"].update(variables)
        return self

    def prompt_variable(self, variable: str, value: object) -> Self:
        self.input_parameters["promptVariables"][variable] = value
        return self
