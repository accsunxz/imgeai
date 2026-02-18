# app/core/context.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class RequestContext:
    """
    请求上下文（单租户/个人订阅产品版）
    - user_id: 登录后才有
    - roles/perms: 可选（你想做 admin 后台/权限系统才需要）
    """
    user_id: Optional[str] = None
    roles: List[str] = None
    perms: Set[str] = None

    @property
    def is_authed(self) -> bool:
        return bool(self.user_id)

    @property
    def is_admin(self) -> bool:
        return "ADMIN" in (self.roles or [])
