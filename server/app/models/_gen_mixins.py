# generated - DO NOT EDIT
from __future__ import annotations

import uuid
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class IdMixin:
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()), comment="ID")


class TimeMixin:
    created_at: Mapped[object] = mapped_column(DateTime(timezone=False), server_default=func.now(), comment="创建时间")
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class SoftDeleteMixin:
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0", comment="软删除")
