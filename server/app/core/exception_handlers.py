# app/core/exception_handlers.py
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.res import Res
from app.common.codes import ResponseCode

ALWAYS_HTTP_200 = True


def _status(code: int) -> int:
    return 200 if ALWAYS_HTTP_200 else code


def register_exception_handlers(app: FastAPI) -> None:
    # 1) 参数校验失败（422）
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, __: RequestValidationError):
        return JSONResponse(
            status_code=_status(422),
            content=Res.fail(ResponseCode._40402).model_dump(),
        )

    # 2) 系统级 HTTP 异常（含 404 Not Found / 405 Method Not Allowed）
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(_: Request, exc: StarletteHTTPException):
        # 你可以按自己的枚举映射
        if exc.status_code == 404:
            code = ResponseCode._5030  # 服务不存在（路由不存在）
        elif exc.status_code == 405:
            code = ResponseCode._40401  # 请求参数格式错误（这里也可单独加一个“方法不支持”码）
        elif exc.status_code == 401:
            code = ResponseCode._4303
        elif exc.status_code == 403:
            code = ResponseCode._4101
        elif exc.status_code == 400:
            code = ResponseCode._40401
        else:
            code = ResponseCode._5050

        return JSONResponse(
            status_code=_status(exc.status_code),
            content=Res.fail(code, msg=str(exc.detail)).model_dump(),
        )

    # 3) 兜底：任何未捕获异常（500）
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, __: Exception):
        return JSONResponse(
            status_code=_status(500),
            content=Res.fail(ResponseCode._5050, msg="服务器内部错误").model_dump(),
        )
