from enum import Enum
from typing import Union, List
from typing_extensions import Self


class StateChangeEventType(Enum):
    onScheduled = 'onScheduled'
    onStart = 'onStart'
    onFailed = 'onFailed'
    onSuccess = 'onSuccess'
    onCancelled = 'onCancelled'


class StateChangeEvent:
    swagger_types = {
        'type': 'str',
        'payload': 'dict[str, object]'
    }

    attribute_map = {
        'type': 'type',
        'payload': 'payload'
    }

    def __init__(self, type: str, payload: dict[str, object]) -> None:
        self._type = type
        self._payload = payload

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type: str) -> Self:
        self._type = type

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, payload: dict[str, object]) -> Self:
        self._payload = payload


class StateChangeConfig:
    swagger_types = {
        'type': 'str',
        'events': 'list[StateChangeEvent]'
    }

    attribute_map = {
        'type': 'type',
        'events': 'events'
    }

    def __init__(self, event_type: Union[str, StateChangeEventType, List[StateChangeEventType]] = None, events: List[StateChangeEvent] = None) -> None:
        if event_type is None:
            return
        if isinstance(event_type, list):
            str_values = []
            for et in event_type:
                str_values.append(et.name)
            self._type = ','.join(str_values)
        else:
            self._type = event_type.name
        self._events = events

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, event_type: StateChangeEventType) -> Self:
        self._type = event_type.name

    @property
    def events(self):
        return self._events

    @events.setter
    def events(self, events: List[StateChangeEvent]) -> Self:
        self._events = events
