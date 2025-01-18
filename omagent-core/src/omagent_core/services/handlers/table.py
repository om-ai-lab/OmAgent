from abc import ABC
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Column, DateTime, Field, SQLModel, func


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
