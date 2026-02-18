# generated - DO NOT EDIT
from __future__ import annotations

from enum import Enum


class UserType(str, Enum):
    ADMIN = "ADMIN"  # 后台管理用户
    CUSTOMER = "CUSTOMER"  # C端注册用户


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"  # 正常
    LOCKED = "LOCKED"  # 锁定
    DISABLED = "DISABLED"  # 禁用


class BasicStatus(str, Enum):
    ENABLE = "ENABLE"  # 正常
    DISABLE = "DISABLE"  # 禁用


class PermType(str, Enum):
    API = "API"  # 接口权限点
    PAGE = "PAGE"  # 页面/路由(可选)
    ACTION = "ACTION"  # 按钮/动作(可选)


class TextMode(str, Enum):
    ZH2EN = "ZH2EN"  # 中文转英文
    EN2ZH = "EN2ZH"  # 英文转中文
