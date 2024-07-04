from abc import ABC
# from sqlalchemy import Column, Text
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, SQLModel, func


class STM(BaseModel):
    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    tasks: Dict = {}
    memory: Dict = {}
    knowledge: Dict = {}
    summary: Dict = {}
    kwargs: Dict = {}


class BaseInterface(BaseModel, ABC):
    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    last_output: Any = None
    kwargs: dict = {}


class BaseTable(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    bot_id: str = Field(index=True, nullable=False)

    create_time: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    update_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )
    )

    deleted: int = 0
