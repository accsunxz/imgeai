# generated - DO NOT EDIT
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class PageQuery(BaseModel):
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    size: int = Field(default=20, ge=1, le=200, description="每页条数")
    order_by: Optional[str] = Field(default=None, description="排序字段，如 created_at desc")


class PageResult(BaseModel, Generic[T]):
    total: int
    items: List[T]


class IdsReq(BaseModel):
    ids: List[str]


class BaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted: Optional[bool] = None
