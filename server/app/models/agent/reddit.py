# app/models/agent/reddit.py
from __future__ import annotations
from typing import Optional, List, Any

from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

# 引入你的基类和 Mixin
from app.models.base import Base
from app.models._gen_mixins import IdMixin, TimeMixin


class RedditLog(IdMixin, TimeMixin, Base):
    """Reddit 风格翻译记录表"""
    __tablename__ = "t_reddit_log"

    # 使用 Mapped 类型注解，保持与 SysUser 一致
    input_text: Mapped[str] = mapped_column(Text, nullable=False, comment="原始中文输入")
    output_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI生成结果")

    # 存储 List[str]，SQLAlchemy 会自动处理 JSON 序列化
    style_refs: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, comment="参考的风格语料")

    status: Mapped[str] = mapped_column(String(20), default="PENDING", comment="状态: PENDING/DONE/ERROR")