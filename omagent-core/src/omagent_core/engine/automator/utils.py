import dataclasses
import datetime
import inspect
import logging
import typing
from typing import List

from dacite import from_dict
from omagent_core.engine.configuration.configuration import Configuration
from requests.structures import CaseInsensitiveDict

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))

simple_types = {int, float, str, bool, datetime.date, datetime.datetime, object}
dict_types = {dict, typing.Dict, CaseInsensitiveDict}
collection_types = {list, List, typing.Set}


def convert_from_dict_or_list(cls: type, data: typing.Union[dict, list]) -> object:
    is_list = type(data) in collection_types
    if is_list:
        val_list = []
        for val in data:
            generic_types = typing.get_args(cls)[0]
            converted = convert_from_dict(generic_types, val)
            val_list.append(converted)
        return val_list
    return convert_from_dict(cls, data)


def convert_from_dict(cls: type, data: dict) -> object:
    if data is None:
        return data

    if type(data) == cls:
        return data

    if dataclasses.is_dataclass(cls):
        return from_dict(data_class=cls, data=data)

    typ = type(data)
    if not (
        (
            str(typ).startswith("dict[")
            or str(typ).startswith("typing.Dict[")
            or str(typ).startswith("requests.structures.CaseInsensitiveDict[")
            or typ == dict
            or str(typ).startswith("OrderedDict[")
        )
    ):
        data = {}

    members = inspect.signature(cls.__init__).parameters
    kwargs = {}

    for member in members:
        if "self" == member:
            continue
        typ = members[member].annotation
        generic_types = typing.get_args(members[member].annotation)

        if typ in simple_types:
            if member in data:
                kwargs[member] = data[member]
            else:
                kwargs[member] = members[member].default
        elif (
            str(typ).startswith("typing.List[")
            or str(typ).startswith("typing.Set[")
            or str(typ).startswith("list[")
        ):
            values = []
            generic_type = object
            if len(generic_types) > 0:
                generic_type = generic_types[0]
            for val in data[member]:
                values.append(get_value(generic_type, val))
            kwargs[member] = values
        elif (
            str(typ).startswith("dict[")
            or str(typ).startswith("typing.Dict[")
            or str(typ).startswith("requests.structures.CaseInsensitiveDict[")
            or typ == dict
            or str(typ).startswith("OrderedDict[")
        ):

            values = {}
            generic_type = object
            if len(generic_types) > 1:
                generic_type = generic_types[1]
            for k in data[member]:
                v = data[member][k]
                values[k] = get_value(generic_type, v)
            kwargs[member] = values
        elif typ == inspect.Parameter.empty:
            if inspect.Parameter.VAR_KEYWORD == members[member].kind:
                if type(data) in dict_types:
                    kwargs.update(data)
                else:
                    kwargs.update(data[member])
            else:
                # kwargs[member] = data[member]
                kwargs.update(data)
        else:
            kwargs[member] = convert_from_dict(typ, data[member])

    return cls(**kwargs)


def get_value(typ: type, val: object) -> object:
    if typ in simple_types:
        return val
    elif (
        str(typ).startswith("typing.List[")
        or str(typ).startswith("typing.Set[")
        or str(typ).startswith("list[")
    ):
        values = []
        for val in val:
            converted = get_value(type(val), val)
            values.append(converted)
        return values
    elif (
        str(typ).startswith("dict[")
        or str(typ).startswith("typing.Dict[")
        or str(typ).startswith("requests.structures.CaseInsensitiveDict[")
        or typ == dict
    ):
        values = {}
        for k in val:
            v = val[k]
            values[k] = get_value(object, v)
        return values
    else:
        return convert_from_dict(typ, val)
