import json
import re
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from ....utils.error import VQLError
from ..base import BotBase

T = TypeVar("T")


class BaseOutputParser(BotBase, ABC, Generic[T]):
    """Class to parse the output of an LLM call.

    Output parsers help structure language model responses.
    """

    regex: Optional[str] = None
    regex_group: Optional[int] = 0

    class Config:
        """Configuration for this pydantic object."""

        extra = "forbid"

    @abstractmethod
    def _parse(self, text: str) -> T:
        """Parse the output of an LLM call.

        A method which takes in a string (assumed output of language model )
        and parses it into some structure.

        Args:
            text: output of language model

        Returns:
            structured output
        """

    def parse(self, text: str) -> T:
        if self.regex:
            regex_res = re.search(self.regex, text)
            if regex_res is not None:
                text = regex_res.group(self.regex_group)
            else:
                raise VQLError(
                    800, detail=f"Not valid json [{text}] for regex [{self.regex}]"
                )
        return self._parse(text)

    @property
    def _type(self) -> str:
        """Return the type key."""
        raise self.type


class DictParser(BaseOutputParser):
    def _fix_json_input(self, input_str: str) -> str:
        # Replace single backslashes with double backslashes,
        # while leaving already escaped ones intact
        corrected_str = re.sub(
            r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r"\\\\", input_str
        )
        corrected_str.replace("'", '"')
        return corrected_str

    def _find_json(self, input_str: str) -> dict:
        match = input_str.find("{")
        result, index = json.JSONDecoder().raw_decode(input_str[match:])
        return result

    def _parse(self, text: str) -> dict:
        try:
            parsed = self._find_json(text)
        except json.JSONDecodeError:
            preprocessed_text = self._fix_json_input(text)
            try:
                parsed = self._find_json(preprocessed_text)
            except Exception:
                raise VQLError(800, detail=f"Not valid json [{text}]")
        return parsed


class ListParser(BaseOutputParser):
    separator: str = ","

    def _parse(self, text: str) -> list:
        res_list = text.split(self.separator)
        res_list = [x.strip() for x in res_list]
        return res_list


class StrParser(BaseOutputParser):
    def _parse(self, text: str) -> str:
        return text
