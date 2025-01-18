from typing import List, Optional

from omagent_core.engine.workflow.task.task import TaskInterface
from omagent_core.engine.workflow.task.task_type import TaskType
from typing_extensions import Self


class LlmTextComplete(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        llm_provider: str,
        model: str,
        prompt_name: str,
        stop_words: Optional[List[str]] = [],
        max_tokens: Optional[int] = 100,
        temperature: int = 0,
        top_p: int = 1,
        task_name: str = None,
    ) -> Self:
        optional_input_params = {}

        if stop_words:
            optional_input_params.update({"stopWords": stop_words})

        if max_tokens:
            optional_input_params.update({"maxTokens": max_tokens})

        if not task_name:
            task_name = "llm_text_complete"

        input_params = {
            "llmProvider": llm_provider,
            "model": model,
            "promptName": prompt_name,
            "promptVariables": {},
            "temperature": temperature,
            "topP": top_p,
        }

        input_params.update(optional_input_params)

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_TEXT_COMPLETE,
            input_parameters=input_params,
        )
        self.input_parameters["promptVariables"] = {}

    def prompt_variables(self, variables: dict[str, object]) -> Self:
        self.input_parameters["promptVariables"].update(variables)
        return self

    def prompt_variable(self, variable: str, value: object) -> Self:
        self.input_parameters["promptVariables"][variable] = value
        return self
