# app/deps.py
from __future__ import annotations

from typing import Any, Dict, Optional, Set, List, Callable, Type, TypeVar, AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

S = TypeVar("S")


# ----------------------------
# DB
# ----------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# ----------------------------
# Auth helpers
# ----------------------------
def _get_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization") or ""
    if not auth:
        return None
    parts = auth.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip().lower(), parts[1].strip()
    if scheme != "bearer" or not token:
        return None
    return token


def _decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def get_current_user_payload(request: Request) -> Optional[Dict[str, Any]]:
    """
    返回 JWT payload（未登录则返回 None）
    """
    token = _get_bearer_token(request)
    if not token:
        return None
    return _decode_jwt(token)


def get_ctx(
    payload: Optional[Dict[str, Any]] = Depends(get_current_user_payload),
) -> RequestContext:
    """
    可匿名上下文：
    - 未登录：user_id=None
    - 登录：从 token payload 取 sub/user_id/uid
    """
    user_id = (payload or {}).get("sub") or (payload or {}).get("user_id") or (payload or {}).get("uid")

    roles: List[str] = list((payload or {}).get("roles") or [])
    perms: Set[str] = set((payload or {}).get("perms") or [])

    return RequestContext(
        user_id=user_id,
        roles=roles,
        perms=perms,
    )


def get_ctx_required(ctx: RequestContext = Depends(get_ctx)) -> RequestContext:
    """
    必须登录：没登录直接 401
    """
    if not ctx.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return ctx


# ----------------------------
# Permission guard
# ----------------------------
def _perm_match(required: str, owned: Set[str]) -> bool:
    """
    支持简单通配：
    - 精确匹配: sys:user:save
    - 前缀通配: sys:user:*  或 sys:*  （owned 里存这种也算）
    - 超级权限: *
    """
    if required in owned:
        return True

    parts = required.split(":")
    for i in range(len(parts), 0, -1):
        prefix = ":".join(parts[:i]) + ":*"
        if prefix in owned:
            return True

    if "*" in owned:
        return True

    return False


def require_perm(perm: str):
    """
    用法（你 codegen 会生成这个）：
      @router.post(..., dependencies=[Depends(get_ctx_required), Depends(require_perm("xxx"))])
      def xxx(...):
          ...
    """

    def _dep(ctx: RequestContext = Depends(get_ctx_required)) -> None:
        # ADMIN 角色直通（可选）
        if ctx.is_admin:
            return

        if not _perm_match(perm, ctx.perms or set()):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return _dep


# ----------------------------
# Service providers (解决你说的 svc = XxxService(db, ctx) 太多的问题)
# ----------------------------
def provide_service(service_cls: Type[S]) -> Callable[..., S]:
    """
    强制登录的 service 注入（用于需要鉴权的接口）
    """
    def _dep(db: Session = Depends(get_db), ctx: RequestContext = Depends(get_ctx_required)) -> S:
        return service_cls(db, ctx)
    return _dep


def provide_service_optional(service_cls: Type[S]) -> Callable[..., S]:
    """
    可匿名的 service 注入（用于公开接口）
    """
    def _dep(db: Session = Depends(get_db), ctx: RequestContext = Depends(get_ctx)) -> S:
        return service_cls(db, ctx)
    return _dep
