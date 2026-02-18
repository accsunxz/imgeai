# generated - DO NOT EDIT
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple, Type, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session


class BaseService:
    def __init__(self, db: Session, ctx: Any):
        self.db = db
        self.ctx = ctx


class CRUDService(BaseService):
    model: Type[Any] = None

    def _base_stmt(self):
        stmt = select(self.model)

        # soft delete
        if hasattr(self.model, "deleted"):
            stmt = stmt.where(self.model.deleted.is_(False))

        return stmt

    def _apply_order_by(self, stmt, order_by: Optional[str]):
        # 安全：只允许 "field" 或 "field asc/desc"
        if not order_by:
            if hasattr(self.model, "created_at"):
                return stmt.order_by(getattr(self.model, "created_at").desc())
            return stmt

        s = (order_by or "").strip()
        if not s:
            return stmt

        parts = s.split()
        field = parts[0].strip()
        direction = (parts[1].strip().lower() if len(parts) > 1 else "asc")

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", field):
            return stmt
        if not hasattr(self.model, field):
            return stmt

        col = getattr(self.model, field)
        if direction == "desc":
            return stmt.order_by(col.desc())
        return stmt.order_by(col.asc())

    def get_by_id(self, obj_id: str):
        stmt = self._base_stmt().where(self.model.id == obj_id)
        return self.db.scalars(stmt).first()

    def create(self, data: Dict[str, Any]):
        obj = self.model(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj_id: str, data: Dict[str, Any]):
        obj = self.get_by_id(obj_id)
        if not obj:
            return None
        for k, v in (data or {}).items():
            if v is None:
                continue
            if hasattr(obj, k):
                setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_many(self, ids: List[str]) -> int:
        n = 0
        for _id in ids or []:
            obj = self.get_by_id(_id)
            if not obj:
                continue
            if hasattr(obj, "deleted"):
                setattr(obj, "deleted", True)
                n += 1
            else:
                self.db.delete(obj)
                n += 1
        self.db.commit()
        return n

    def list(self, filters: Optional[Dict[str, Any]] = None, order_by: Optional[str] = None) -> List[Any]:
        stmt = self._base_stmt()
        filters = filters or {}
        for k, v in filters.items():
            if v is None:
                continue
            if hasattr(self.model, k):
                stmt = stmt.where(getattr(self.model, k) == v)
        stmt = self._apply_order_by(stmt, order_by)
        return list(self.db.scalars(stmt).all())

    def paging(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        size: int = 20,
        order_by: Optional[str] = None,
    ) -> Tuple[int, List[Any]]:
        stmt = self._base_stmt()
        filters = filters or {}

        for k, v in filters.items():
            if v is None:
                continue
            if hasattr(self.model, k):
                stmt = stmt.where(getattr(self.model, k) == v)

        stmt = self._apply_order_by(stmt, order_by)

        subq = stmt.subquery()
        total = self.db.scalar(select(func.count()).select_from(subq)) or 0
        items = list(self.db.scalars(stmt.offset((page - 1) * size).limit(size)).all())
        return int(total), items
