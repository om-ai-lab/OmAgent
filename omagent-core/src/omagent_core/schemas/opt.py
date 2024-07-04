from enum import Enum


class ChatStatus(str, Enum):
    INCOMPLETE = "incomplete"
    END_BLOCK = "end_block"
    END_ANSWER = "end_answer"


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    THINKING = "thinking"


class MessageType(str, Enum):
    IMAGE = "image"
    TEXT = "text"
    File = "file"
    MIXED = "mixed"


class SrcType(str, Enum):
    TEXT = "text"
    URL = "url"
    BASE64 = "base64"
    REDIS = "redis"
    LOCAL = "local"


class OPT:
    CHAT_STATUS = ChatStatus
    ROLE = Role
    MESSAGE_TYPE = MessageType
    SRC_TYPE = SrcType
