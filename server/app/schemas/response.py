# app/schemas/response.py
from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ResponseData(BaseModel, Generic[T]):
    """
    统一响应结构（匹配 app/common/res.py）：
      {
        "code": 0,
        "status": "ok" | "error",
        "message": "xxx",
        "body": <T | null>
      }
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    code: int
    status: str
    message: str
    body: Optional[T] = None
