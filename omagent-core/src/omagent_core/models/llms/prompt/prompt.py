from __future__ import annotations

from pathlib import Path
import os
from string import Formatter
from typing import Any, Dict, List, Union

from pydantic import model_validator

from ....utils.registry import registry
from .base import (DEFAULT_FORMATTER_MAPPING, BasePromptTemplate,
                   _get_jinja2_variables_from_template, check_valid_template)


@registry.register_prompt()
class PromptTemplate(BasePromptTemplate):
    """Schema to represent a prompt for an LLM.

    Example:
        .. code-block:: python

            prompt = PromptTemplate(input_variables=["foo"], template="Say {foo}")
    """

    # input_variables: List[str]
    template: str
    """The prompt template."""

    template_format: str = "jinja2"
    """The format of the prompt template. Options are: 'f-string', 'jinja2'."""

    validate_template: bool = True
    """Whether or not to try validating the template."""

    role: str = "user"

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        input_variables = kwargs.get("input_variables", [])
        pre_filled_kv = {key: kwargs[key] for key in input_variables if key in kwargs.keys()}
        if pre_filled_kv:
            self.template = self.format(**pre_filled_kv)
            input_variables = list(set(input_variables) - set(pre_filled_kv.keys()))
            self.input_variables = input_variables

    def format(self, **kwargs: Any) -> str:
        """Format the prompt with the inputs.

        Args:
            kwargs: Any arguments to be passed to the prompt template.

        Returns:
            A formatted string.

        Example:

        .. code-block:: python

            prompt.format(variable1="foo")
        """
        kwargs = self._merge_partial_and_user_variables(**kwargs)
        return DEFAULT_FORMATTER_MAPPING[self.template_format].format(
            self.template, **kwargs
        )

    @model_validator(mode="after")
    def template_is_valid(self) -> "PromptTemplate":
        """Check that template and input variables are consistent."""
        if self.validate_template:
            all_inputs = self.input_variables + list(self.partial_variables)
            check_valid_template(self.template, self.template_format, all_inputs)
        return self

    @classmethod
    def from_examples(
        cls,
        examples: List[str],
        suffix: str,
        input_variables: List[str],
        example_separator: str = "\n\n",
        prefix: str = "",
        **kwargs: Any,
    ) -> PromptTemplate:
        """Take examples in list format with prefix and suffix to create a prompt.

        Intended to be used as a way to dynamically create a prompt from examples.

        Args:
            examples: List of examples to use in the prompt.
            suffix: String to go after the list of examples. Should generally
                set up the user's input.
            input_variables: A list of variable names the final prompt template
                will expect.
            example_separator: The separator to use in between examples. Defaults
                to two new line characters.
            prefix: String that should go before any examples. Generally includes
                examples. Default to an empty string.

        Returns:
            The final prompt generated.
        """
        template = example_separator.join([prefix, *examples, suffix])
        return cls(input_variables=input_variables, template=template, **kwargs)

    @classmethod
    def find_file(cls, start_dir, file_name):
        for root, dirs, files in os.walk(start_dir):
            if file_name in files:
                return os.path.join(root, file_name)
        return None

    @classmethod
    def from_file(
        cls, template_file: Union[str, Path], **kwargs: Any
    ) -> PromptTemplate:
        """Load a prompt from a file.

        Args:
            template_file: The path to the file containing the prompt template.
            input_variables: A list of variable names the final prompt template
                will expect.
        Returns:
            The prompt loaded from the file.
        """
        original_file = template_file
        while True:
            if os.path.exists(template_file):
                with open(template_file, "r") as f:
                    template = f.read()
                return cls.from_template(template=template, **kwargs)
            
            if "/" in template_file:
                template_file = "/".join(template_file.split("/", 1)[1:])
            else:
                raise ValueError(f"the prompt file path ({original_file}) is not valid")

    @classmethod
    def from_template(
        cls, template: str, template_format: str = "jinja2", **kwargs: Any
    ) -> PromptTemplate:
        """Load a prompt template from a template."""
        if template_format == "jinja2":
            # Get the variables for the template
            input_variables = _get_jinja2_variables_from_template(template)

        else:
            input_variables = {
                v for _, v, _, _ in Formatter().parse(template) if v is not None
            }

        return cls(
            input_variables=list(sorted(input_variables)),
            template=template,
            template_format=template_format,
            **kwargs,
        )

    @classmethod
    def from_config(cls, config: Dict) -> PromptTemplate:
        """Load a prompt template from a config."""
        template = config.pop("template")
        if template.endswith(".prompt"):
            return cls.from_file(template, **config)
        else:
            return cls.from_template(template, **config)
