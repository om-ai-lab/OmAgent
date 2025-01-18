from pydantic import BaseModel

from ..utils.registry import registry
from .base import BaseTool


def simple_tool(
    name: str = None,
    description: str = None,
    args_schema: BaseModel = None,
    special_params: dict = {},
):
    """A decorator that generates a tool based on a function.

    Args:
        name (str, optional): The name of this tool. Defaults to the function name.
        description (str, optional): The description of what this tool is for. Defaults to the function doc.
        args_schema (BaseModel, optional): A schema of the tool's input. If this is specified,the input will be check and transfer to this object. Defaults to None.
        special_params (dict, optional): Some parameters that the tool may need for execution. Defaults to {}.
    """

    def wrapper(
        func,
        name=name,
        description=description,
        args_schema=args_schema,
        special_params=special_params,
    ):
        if name == None:
            name = func.__name__
        if description == None and func.__doc__:
            description = func.__doc__
        elif description == None and func.__doc__ == None:
            raise ValueError(
                'One of arg "description" or the function doc need to be valid intro.'
            )
        new_tool = BaseTool(
            name=name,
            description=description,
            func=func,
            args_schema=args_schema,
            special_params=special_params,
        )
        registry.mapping["tool"][name] = new_tool

        def inner_wrapper(*args, **kwargs):
            return new_tool.run(*args, **kwargs)

        return inner_wrapper

    return wrapper
