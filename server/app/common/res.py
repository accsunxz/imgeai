from __future__ import annotations
from typing import TypeVar, Optional
from app.schemas.response import ResponseData
from app.common.codes import ResponseCode

T = TypeVar("T")

SUCCESS_STATUS = "ok"
ERROR_STATUS = "error"

class Res:
    @staticmethod
    def success(body: Optional[T] = None, code: ResponseCode = ResponseCode._0000, msg: str | None = None) -> ResponseData[T]:
        return ResponseData[T](
            code=code.code,
            status=SUCCESS_STATUS,
            message=msg or code.msg,
            body=body,
        )

    @staticmethod
    def fail(code: ResponseCode = ResponseCode._5050, msg: str | None = None) -> ResponseData[None]:
        return ResponseData[None](
            code=code.code,
            status=ERROR_STATUS,
            message=msg or code.msg,
            body=None,
        )
