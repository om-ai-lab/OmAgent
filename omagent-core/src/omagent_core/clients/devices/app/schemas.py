from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class CodeEnum(int, Enum):
    SUCCESS = 0

class ContentItem(BaseModel):
    type: str
    resource_id: Optional[str]
    data: str

class InputMessage(BaseModel):
    role: str
    content: List[ContentItem]

class ChatRequest(BaseModel):
    agent_id: str
    messages: List[InputMessage]
    kwargs: Dict[str, Any] = {}
    

class CallbackMessage(BaseModel):
    role: str
    type: str
    content: str

class Usage(BaseModel):
    prompt_tokens: int
    output_tokens: int
    
class ContentStatus(str, Enum):
    INCOMPLETE = "incomplete" # the conversation content is not yet complete
    END_BLOCK = "end_block" # a single conversation has ended, but the overall result is not finished
    END_ANSWER = "end_answer" # the overall return is complete


class ChatResponse(BaseModel):
    agent_id: str
    code: int
    error_info: str
    took: int
    content_status: ContentStatus
    message: CallbackMessage
    usage: Usage
    
class RunningInfo(BaseModel):
    agent_id: str
    progress: str
    message: Optional[str]

class DataMemorize(BaseModel):
    content: List[ContentItem]
    

class ContentStatus(str, Enum):
    INCOMPLETE = "incomplete" # the conversation content is not yet complete
    END_BLOCK = "end_block" # a single conversation has ended, but the overall result is not finished
    END_ANSWER = "end_answer" # the overall return is complete

class InteractionType(int, Enum):
    DEFAULT = 0
    INPUT = 1

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE_URL = "image_url"
    IMAGE_BASE64 = "image_base64"