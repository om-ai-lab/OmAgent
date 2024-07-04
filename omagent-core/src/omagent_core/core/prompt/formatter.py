from abc import ABC, abstractmethod
from string import Formatter
from typing import Any, List, Mapping, Sequence, Set, Union


class BaseFormatter(ABC):
    @abstractmethod
    def format(self, template: str, **kwargs: Any) -> str:
        """Format a template."""

    @abstractmethod
    def validate(self, template: str, input_variables: List[str]) -> None:
        """Validate a template."""


class FStringFormatter(Formatter, BaseFormatter):
    """A subclass of formatter that checks for extra keys."""

    def check_unused_args(
        self,
        used_args: Sequence[Union[int, str]],
        args: Sequence,
        kwargs: Mapping[str, Any],
    ) -> None:
        """Check to see if extra parameters are passed."""
        extra = set(kwargs).difference(used_args)
        if extra:
            raise KeyError(extra)

    def vformat(
        self, format_string: str, args: Sequence, kwargs: Mapping[str, Any]
    ) -> str:
        """Check that no arguments are provided."""
        if len(args) > 0:
            raise ValueError(
                "No arguments should be provided, "
                "everything should be passed as keyword arguments."
            )
        return super().vformat(format_string, args, kwargs)

    def validate(self, template: str, input_variables: List[str]) -> None:
        dummy_inputs = {input_variable: "foo" for input_variable in input_variables}
        super().format(template, **dummy_inputs)


class JinjiaFormatter(BaseFormatter):
    def format(self, template: str, **kwargs: Any) -> str:
        """Format a template using jinja2."""
        try:
            from jinja2 import Template
        except ImportError:
            raise ImportError(
                "jinja2 not installed, which is needed to use the jinja2_formatter. "
                "Please install it with `pip install jinja2`."
            )

        return Template(template).render(**kwargs)

    def validate(self, template: str, input_variables: List[str]) -> None:
        input_variables_set = set(input_variables)
        valid_variables = self._get_jinja2_variables_from_template(template)
        missing_variables = valid_variables - input_variables_set
        extra_variables = input_variables_set - valid_variables

        error_message = ""
        if missing_variables:
            error_message += f"Missing variables: {missing_variables} "

        if extra_variables:
            error_message += f"Extra variables: {extra_variables}"

        if error_message:
            raise KeyError(error_message.strip())

    def _get_jinja2_variables_from_template(self, template: str) -> Set[str]:
        try:
            from jinja2 import Environment, meta
        except ImportError:
            raise ImportError(
                "jinja2 not installed, which is needed to use the jinja2_formatter. "
                "Please install it with `pip install jinja2`."
            )
        env = Environment()
        ast = env.parse(template)
        variables = meta.find_undeclared_variables(ast)
        return variables
