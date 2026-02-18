# app/models/base.py
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    所有 ORM Model 的统一基类。
    重点：必须只有一个 Base，所有表都继承它，才能共享同一个 metadata/registry。
    """
    pass
