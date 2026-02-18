from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

@dataclass(frozen=True)
class ResType:
    code: str
    msg: str

class ResponseCode(Enum):
    _0000 = ResType("0000", "请求成功")

    _5050 = ResType("5050", "请求失败")
    _5030 = ResType("5030", "服务不存在")

    _40401 = ResType("40401", "请求参数格式错误")
    _40402 = ResType("40402", "参数校验失败")
    _40403 = ResType("40403", "没有信息")

    _4101 = ResType("4101", "没有该权限")

    _4301 = ResType("4301", "token为空")
    _4302 = ResType("4302", "token验证过期")
    _4303 = ResType("4303", "token验证失败 不合法的令牌")

    _4401 = ResType("4401", "该用户不存在")
    _4402 = ResType("4402", "用户名或密码错误")
    _4403 = ResType("4403", "账号已禁用")
    _4404 = ResType("4404", "账号已锁定")
    _4405 = ResType("4405", "该用户已存在")
    _4410 = ResType("4410", "登录失败")

    _9901 = ResType("9901", "时间转换错误")

    @property
    def code(self) -> str:
        return self.value.code

    @property
    def msg(self) -> str:
        return self.value.msg

    @classmethod
    def get_enum(cls, code: str) -> "ResponseCode | None":
        for e in cls:
            if e.code == code:
                return e
        return None

    @classmethod
    def get_msg(cls, code: str) -> str | None:
        e = cls.get_enum(code)
        return e.msg if e else None
