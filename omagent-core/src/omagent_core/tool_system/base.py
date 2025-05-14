import json
from abc import ABC
from distutils.util import strtobool
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml
from omagent_core.base import BotBase
from omagent_core.models.od.schemas import Target
from omagent_core.services.handlers.sql_data_handler import SQLDataHandler
from omagent_core.utils.error import VQLError
from omagent_core.utils.logger import logging
from omagent_core.utils.plot import Annotator
from PIL import Image
from pydantic import BaseModel, model_validator


class ArgSchema(BaseModel):
    """ArgSchema defines the tool input schema. Only support one layer definition. Please prevent using complex structure."""

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    class ArgInfo(BaseModel):
        description: Optional[str]
        type: str = "str"
        enum: Optional[List] = None
        required: Optional[bool] = True

    @model_validator(mode="before")
    @classmethod
    def validate_all(cls, values):
        for key, value in values.items():
            if type(value) is str:
                values[key] = cls.ArgInfo(name=value)
            elif type(value) is dict:
                values[key] = cls.ArgInfo(**value)
            elif type(value) is cls.ArgInfo:
                pass
            else:
                raise ValueError(
                    "The arg type must be one of string, dict or self.ArgInfo."
                )
        return values

    @classmethod
    def from_file(cls, schema_file: Union[str, Path]):
        if type(schema_file) is str:
            schema_file = Path(schema_file)
        if schema_file.suffix == ".json":
            with open(schema_file, "r") as f:
                schema = json.load(f)
        elif schema_file.suffix == ".yaml":
            with open(schema_file, "r") as f:
                schema = yaml.load(f, Loader=yaml.FullLoader)
        else:
            raise ValueError("Only support json and yaml file.")
        return cls(**schema)

    def generate_schema(self) -> Union[dict, list]:
        required_args = []
        parameters = {}
        for key, value in self.model_dump(exclude_none=True).items():
            parameters[key] = value
            if parameters[key].pop("required"):
                required_args.append(key)
        return parameters, required_args

    def validate_args(self, args: dict) -> dict:
        if type(args) is not dict:
            raise ValueError(
                "ArgSchema validate only support dict, not {}".format(type(args))
            )
        new_args = {}
        required_fields = set(
            [k for k, v in self.model_dump().items() if v["required"]]
        )
        name_mapping = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
        }
        for name, value in args.items():
            if name not in self.model_dump():
                logging.warning(
                    "The input args includes an unnecessary parameter {}. Removed from the args.".format(
                        name
                    )
                )
                continue
            if name_mapping[type(value).__name__] == self.model_dump()[name]["type"]:
                if (
                    self.model_dump()[name]["enum"]
                    and value not in self.model_dump()[name]["enum"]
                ):
                    raise ValueError(
                        "The value of {} should be one of {}, but got {}".format(
                            name, str(self.model_dump()[name]["enum"]), value
                        )
                    )
                new_args[name] = value
            elif self.model_dump()[name]["type"] == "string":
                try:
                    new_args[name] = str(value)
                except:
                    raise ValueError(
                        "Parameter {} type expect a str value, but got a {} {}".format(
                            name, type(value), value
                        )
                    )
            elif self.model_dump()[name]["type"] == "integer":
                try:
                    new_args[name] = int(value)
                except:
                    raise ValueError(
                        "Parameter {} type expect an int value, but got a {} {}".format(
                            name, type(value), value
                        )
                    )
            elif self.model_dump()[name]["type"] == "number":
                try:
                    new_args[name] = float(value)
                except:
                    raise ValueError(
                        "Parameter {} type expect a float value, but got a {} {}".format(
                            name, type(value), value
                        )
                    )
            elif self.model_dump()[name]["type"] == "boolean":
                if type(value) is bool:
                    new_args[name] = value
                else:
                    try:
                        new_args[name] = strtobool(str(value))
                    except:
                        raise ValueError(
                            "Parameter {} type expect a boolean value, but got a {} {}".format(
                                name, type(value), value
                            )
                        )
            else:
                raise ValueError(
                    "Parameter {} type expect one of string, integer, number and boolean, but got a {} {}".format(
                        name, self.model_dump()[name]["type"], type(value), value
                    )
                )

        if required_fields - set(new_args.keys()):
            raise VQLError(
                "The required fields {} are missing.".format(
                    required_fields - set(new_args.keys())
                )
            )
        return new_args


class BaseTool(BotBase, ABC):
    description: str
    func: Optional[Callable] = None
    args_schema: Optional[ArgSchema]
    special_params: Dict = {}

    def model_post_init(self, __context: Any) -> None:
        for _, attr_value in self.__dict__.items():
            if isinstance(attr_value, BotBase):
                attr_value._parent = self

    @property
    def workflow_instance_id(self) -> str:
        if hasattr(self, "_parent"):
            return self._parent.workflow_instance_id
        return None

    @workflow_instance_id.setter
    def workflow_instance_id(self, value: str):
        if hasattr(self, "_parent"):
            self._parent.workflow_instance_id = value

    def _run(self, **input) -> str:
        """Implement this function or pass 'func' arg when initializing."""
        return self.func(**input)

    async def _arun(self, **input) -> str:
        """Implement this function or pass 'func' arg when initializing."""
        return await self.func(**input)

    def run(self, input: Any) -> str:
        if self.args_schema != None:
            if type(input) != dict:
                raise ValueError(
                    "The input type must be dict when args_schema is specified."
                )
            self.args_schema.validate_args(input)
        return self._run(**input, **self.special_params)

    async def arun(self, input: Any) -> str:
        if self.args_schema != None:
            if type(input) != dict:
                raise ValueError(
                    "The input type must be dict when args_schema is specified."
                )
            self.args_schema.validate_args(input)
        return await self._arun(**input, **self.special_params)

    def generate_schema(self):
        if not self.args_schema:
            return {
                "type": "function",
                "description": self.description,
                "function": {
                    "name": self.name,
                    "parameters": {
                        "type": "object",
                        "name": "input",
                        "required": ["input"],
                    },
                },
            }
        else:
            properties, required = self.args_schema.generate_schema()
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            }


class BaseModelTool(BaseTool, ABC):
    # data_handler: Optional[SQLDataHandler]

    def visual_prompting(
        self,
        image: Image.Image,
        annotation: List[Target],
        prompting_type: str = "label_on_img",
        include_labels: Union[List, set, tuple] = None,
        exclude_labels: Union[List, set, tuple] = None,
    ) -> List[Image.Image]:
        annotator = Annotator(image)
        for obj in annotation:
            if (exclude_labels is not None and obj.label in exclude_labels) or (
                include_labels is not None and obj.label not in include_labels
            ):
                continue
            if obj.bbox:
                annotator.box_label(obj.bbox, obj.label, color="red")
            # TODO: Add polygon support
        return annotator.result()

    def infer(self, images: List[Image.Image], kwargs) -> List[List[Target]]:
        """The model inference step. Only support OD type detection.

        Args:
            images (List[Image.Image]): The list of input images. Image should be PIL Image object.
            kwargs (dict): The additional arguments for the model.

        Returns:
            List[List[Target]]: The detection results.
        """

    def ainfer(self, images: List[Image.Image], kwargs) -> List[List[Target]]:
        """The async version of model inference step. Only support OD type detection.

        Args:
            images (List[Image.Image]): The list of input images. Image should be PIL Image object.
            kwargs (dict): The additional arguments for the model.

        Returns:
            List[List[Target]]: The detection results.
        """


class MemoryTool(BaseTool):
    memory_handler: Optional[SQLDataHandler]

    def generate_schema(self) -> dict:
        """Generate the data table schema in dict format.

        Returns:
            dict: The data table schema. Including the table name, and the name, data type and additional information of each column.
        """
        table = self.memory_handler.table
        schema = {"table_name": table.__tablename__, "columns": []}
        for column in table.__table__.columns:
            schema["columns"].append(
                {
                    "name": column.name,
                    "type": column.type.__visit_name__,
                    "info": column.info,
                }
            )
        return schema

    def generate_prompt(self):
        pass

    def _run(self):
        self.memory_handler.execute_sql()

    async def _arun(self):
        self.memory_handler.execute_sql()