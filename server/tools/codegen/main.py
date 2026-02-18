# tools/codegen/main.py
from __future__ import annotations

import argparse
import json
import re
import shutil
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


GEN_HEADER = "# generated - DO NOT EDIT"
DIR_MARKER = ".codegen"  # clean 时只删带 marker 的目录


# -------------------------
# Utils
# -------------------------
def snake_case(name: str) -> str:
    if not name:
        return name
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.replace("-", "_").lower()


def title_case(name: str) -> str:
    parts = re.split(r"[_\-\s]+", (name or "").strip())
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def ensure_init_py(p: Path) -> None:
    ensure_dir(p)
    init_file = p / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# package\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def py_str(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


def parse_import_target(s: str) -> Tuple[str, List[str]]:
    """
    "module:Name" -> ("module", ["Name"])
    "module:a,b,c" -> ("module", ["a","b","c"])
    """
    if ":" not in s:
        raise ValueError(f"Invalid import target: {s} (expect module:Name)")
    mod, names = s.split(":", 1)
    name_list = [x.strip() for x in names.split(",") if x.strip()]
    if not mod.strip() or not name_list:
        raise ValueError(f"Invalid import target: {s}")
    return mod.strip(), name_list


def guess_entity_file_stem(class_name: str, module_name: str) -> str:
    # 贴近你项目习惯：SysUser -> user.py
    if module_name == "sys" and class_name.startswith("Sys") and len(class_name) > 3:
        return snake_case(class_name[3:])
    return snake_case(class_name)


def mark_codegen_dir(dir_path: Path, spec_path: Path) -> None:
    ensure_dir(dir_path)
    (dir_path / DIR_MARKER).write_text(f"generated from: {spec_path.as_posix()}\n", encoding="utf-8")


def is_generated_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        head = path.read_text(encoding="utf-8").lstrip()[:80]
        return head.startswith(GEN_HEADER)
    except Exception:
        return False


# -------------------------
# Config
# -------------------------
@dataclass
class CodegenConfig:
    app_dir: str = "app"
    app_pkg: str = "app"

    gen_paths: Dict[str, str] = None
    imports: Dict[str, str] = None

    api_prefix_template: str = "/{module}/{entity}"
    api_tag_template: str = "{module}:{entity}"

    def __post_init__(self):
        if self.gen_paths is None:
            self.gen_paths = {
                "enums": "enums",
                "models": "models",
                "schemas": "schemas",
                "services": "services",
                "api": "api",
            }
        if self.imports is None:
            self.imports = {
                "base": f"{self.app_pkg}.models.base:Base",
                "deps": f"{self.app_pkg}.deps:get_db,get_ctx,get_ctx_required,require_perm,provide_service,provide_service_optional",
                "res": f"{self.app_pkg}.common.res:Res",
            }

    @staticmethod
    def load(path: Optional[Path]) -> "CodegenConfig":
        cfg = CodegenConfig()
        if not path:
            return cfg
        raw = read_json(path)
        if not isinstance(raw, dict):
            return cfg

        cfg.app_dir = raw.get("app_dir", cfg.app_dir)
        cfg.app_pkg = raw.get("app_pkg", cfg.app_pkg)

        gp = raw.get("gen_paths")
        if isinstance(gp, dict):
            cfg.gen_paths = {**cfg.gen_paths, **gp}

        im = raw.get("imports")
        if isinstance(im, dict):
            cfg.imports = {**cfg.imports, **im}

        api = raw.get("api")
        if isinstance(api, dict):
            cfg.api_prefix_template = api.get("prefix_template", cfg.api_prefix_template)
            cfg.api_tag_template = api.get("tag_template", cfg.api_tag_template)

        return cfg


# -------------------------
# Spec models
# -------------------------
@dataclass
class EnumDef:
    name: str
    values: List[Tuple[str, str]]  # (value, comment)


@dataclass
class FieldDef:
    name: str
    type: str
    not_null: bool
    length: Optional[int] = None
    enum_name: Optional[str] = None
    default_value: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class ApiParamDef:
    name: str
    type: str
    required: bool
    comment: Optional[str] = None
    enum_name: Optional[str] = None


@dataclass
class ApiDef:
    name: str
    summary: str
    path: str
    param_mode: str  # ENTITY / QUERY / IDS / CUSTOM
    dto_name: Optional[str] = None
    params: Optional[List[ApiParamDef]] = None
    required_perms: Optional[List[str]] = None  # ✅ 非空才做权限校验
    auth_required: bool = False  # ✅ 只要为 true，就要求登录（即使 requiredPerms 为空）


@dataclass
class EntityDef:
    class_name: str
    table_name: str
    module_name: str
    comment: str
    zn_name: str
    fields: List[FieldDef]
    unique_constraints: List[Tuple[str, List[str]]]
    apis: List[ApiDef]


@dataclass
class Spec:
    enums: Dict[str, EnumDef]
    entities: List[EntityDef]


# -------------------------
# Load & normalize spec
# -------------------------
def collect_enums_from_entity_list(raw_entities: List[Dict[str, Any]]) -> Dict[str, EnumDef]:
    enums: Dict[str, EnumDef] = {}
    for e in raw_entities:
        for f in e.get("fields", []) or []:
            if f.get("type") == "enum":
                enum_name = f.get("enumName")
                enum_values = f.get("enumValues") or []
                if enum_name and enum_name not in enums:
                    vals: List[Tuple[str, str]] = []
                    for it in enum_values:
                        vals.append((str(it.get("value")), str(it.get("comment") or "")))
                    enums[enum_name] = EnumDef(name=enum_name, values=vals)
    return enums


def normalize_entities(raw_entities: List[Dict[str, Any]], enums: Dict[str, EnumDef]) -> List[EntityDef]:
    entities: List[EntityDef] = []
    for e in raw_entities:
        class_name = str(e.get("className"))
        table_name = str(e.get("tableName"))
        module_name = str(e.get("moduleName") or "biz")
        comment = str(e.get("comment") or "")
        zn_name = str(e.get("znName") or class_name)

        fields: List[FieldDef] = []
        for f in e.get("fields", []) or []:
            f_type = str(f.get("type"))
            fields.append(
                FieldDef(
                    name=str(f.get("name")),
                    type=f_type,
                    not_null=bool(f.get("notNull", False)) if f.get("notNull") is not None else False,
                    length=(int(f.get("length")) if f.get("length") is not None else None),
                    enum_name=(str(f.get("enumName")) if f_type == "enum" else None),
                    default_value=(str(f.get("defaultValue")) if f.get("defaultValue") is not None else None),
                    comment=(str(f.get("comment")) if f.get("comment") is not None else None),
                )
            )

        uniques: List[Tuple[str, List[str]]] = []
        for uc in e.get("uniqueConstraints", []) or []:
            name = str(uc.get("name") or "")
            cols = [snake_case(c) for c in (uc.get("columns") or [])]
            uniques.append((name, cols))

        apis: List[ApiDef] = []
        for a in e.get("apis", []) or []:
            param_mode = str(a.get("paramMode") or "ENTITY").upper()
            params = None
            if param_mode == "CUSTOM":
                params = []
                for p in a.get("params", []) or []:
                    p_type = str(p.get("type"))
                    params.append(
                        ApiParamDef(
                            name=str(p.get("name")),
                            type=p_type,
                            required=bool(p.get("required", False)),
                            comment=str(p.get("comment") or ""),
                            enum_name=str(p.get("enumName")) if p_type == "enum" else None,
                        )
                    )

            required_perms = a.get("requiredPerms")
            if required_perms is not None:
                required_perms = [str(x) for x in required_perms if str(x).strip()]

            apis.append(
                ApiDef(
                    name=str(a.get("name")),
                    summary=str(a.get("summary") or a.get("name")),
                    path=str(a.get("path") or ("/" + str(a.get("name")))),
                    param_mode=param_mode,
                    dto_name=str(a.get("dtoName")) if a.get("dtoName") else None,
                    params=params,
                    required_perms=required_perms,
                    auth_required=bool(a.get("authRequired", False)),  # ✅ 登录但不必有权限
                )
            )

        entities.append(
            EntityDef(
                class_name=class_name,
                table_name=table_name,
                module_name=module_name,
                comment=comment,
                zn_name=zn_name,
                fields=fields,
                unique_constraints=uniques,
                apis=apis,
            )
        )
    return entities


def load_spec(spec_path: Path) -> Spec:
    raw = read_json(spec_path)

    if isinstance(raw, list):
        raw_entities = raw
        enums = collect_enums_from_entity_list(raw_entities)
        entities = normalize_entities(raw_entities, enums)
        return Spec(enums=enums, entities=entities)

    if isinstance(raw, dict):
        enums: Dict[str, EnumDef] = {}
        raw_enums = raw.get("enums") or {}
        for en_name, arr in raw_enums.items():
            vals: List[Tuple[str, str]] = []
            for it in arr or []:
                vals.append((str(it.get("value")), str(it.get("comment") or "")))
            enums[en_name] = EnumDef(name=en_name, values=vals)

        raw_entities = raw.get("entities") or raw.get("modules") or []
        if isinstance(raw_entities, list):
            enums2 = collect_enums_from_entity_list(raw_entities)
            for k, v in enums2.items():
                enums.setdefault(k, v)
            entities = normalize_entities(raw_entities, enums)
            return Spec(enums=enums, entities=entities)

    raise ValueError("Unsupported spec JSON format. Expect a list[] or an object{enums,entities}.")


# -------------------------
# Render helpers
# -------------------------
def sa_type_expr(f: FieldDef) -> str:
    t = f.type
    if t == "String":
        if f.length is None or f.length <= 0:
            return "Text"
        return f"String({int(f.length)})"
    if t == "Integer":
        return "Integer"
    if t == "Long":
        return "BigInteger"
    if t == "Boolean":
        return "Boolean"
    if t == "LocalDateTime":
        return "DateTime(timezone=False)"
    if t == "Json":
        return "JSON"
    if t == "enum":
        return f"SAEnum({f.enum_name}, name='enum_{snake_case(f.enum_name or 'x')}', native_enum=False)"
    # 其它未知类型统一落到 Text
    return "Text"


_LIST_RE = re.compile(r"^List<\s*([A-Za-z0-9_]+)\s*>$")


def py_type_hint_by_type(t: str, enum_name: Optional[str] = None) -> str:
    """
    生成 Pydantic / DTO 的类型提示
    - 支持 Json -> Dict[str, Any]
    - 支持 List<String> 等 -> List[str]
    """
    if t == "String":
        return "str"
    if t == "Integer":
        return "int"
    if t == "Long":
        return "int"
    if t == "Boolean":
        return "bool"
    if t == "LocalDateTime":
        return "datetime"
    if t == "Json":
        return "Dict[str, Any]"
    if t == "enum":
        return enum_name or "str"

    m = _LIST_RE.match(t or "")
    if m:
        inner = m.group(1)
        inner_hint = py_type_hint_by_type(inner)
        return f"List[{inner_hint}]"

    return "Any"


def py_type_hint_field(f: FieldDef) -> str:
    return py_type_hint_by_type(f.type, f.enum_name)


# -------------------------
# Render: files
# -------------------------
def render_enums_file(spec: Spec) -> str:
    lines = [
        GEN_HEADER,
        "from __future__ import annotations",
        "",
        "from enum import Enum",
        "",
        "",
    ]
    for enum_name, enum_def in spec.enums.items():
        lines.append(f"class {enum_name}(str, Enum):")
        if not enum_def.values:
            lines.append("    pass")
        else:
            for v, c in enum_def.values:
                key = re.sub(r"[^A-Za-z0-9_]", "_", str(v))
                key = key if re.match(r"^[A-Za-z_]", key) else f"V_{key}"
                lines.append(f'    {key} = "{py_str(v)}"  # {c}')
        lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_mixins_file() -> str:
    return textwrap.dedent(
        f"""
        {GEN_HEADER}
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
        """
    ).strip() + "\n"


def render_schema_common() -> str:
    return textwrap.dedent(
        f"""
        {GEN_HEADER}
        from __future__ import annotations

        from datetime import datetime
        from typing import Any, Dict, Generic, List, Optional, TypeVar

        from pydantic import BaseModel, ConfigDict, Field


        T = TypeVar("T")


        class PageQuery(BaseModel):
            page: int = Field(default=1, ge=1, description="页码，从1开始")
            size: int = Field(default=20, ge=1, le=200, description="每页条数")
            order_by: Optional[str] = Field(default=None, description="排序字段，如 created_at desc")


        class PageResult(BaseModel, Generic[T]):
            total: int
            items: List[T]


        class IdsReq(BaseModel):
            ids: List[str]


        class BaseRead(BaseModel):
            model_config = ConfigDict(from_attributes=True)

            id: str
            created_at: Optional[datetime] = None
            updated_at: Optional[datetime] = None
            deleted: Optional[bool] = None
        """
    ).strip() + "\n"


def render_service_base() -> str:
    return textwrap.dedent(
        f"""
        {GEN_HEADER}
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
                for k, v in (data or {{}}).items():
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
                filters = filters or {{}}
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
                filters = filters or {{}}

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
        """
    ).strip() + "\n"


def render_model_file(
    ent: EntityDef,
    enums_module: str,
    mixins_module: str,
    base_import: Tuple[str, str],
) -> str:
    base_mod, base_name = base_import

    mixins = ["IdMixin", "TimeMixin", "SoftDeleteMixin"]

    col_lines = []
    for f in ent.fields:
        colname = snake_case(f.name)
        nullable = "False" if f.not_null else "True"

        default_expr = ""
        if f.default_value is not None:
            dv = str(f.default_value).strip()
            if dv.lower() in ("true", "false"):
                default_expr = f", default={dv.lower() == 'true'}"
            elif re.fullmatch(r"-?\d+", dv):
                default_expr = f", default={int(dv)}"
            else:
                default_expr = f', default="{py_str(dv)}"'

        comment = f', comment="{py_str(f.comment or "")}"' if f.comment else ""
        typ = sa_type_expr(f)
        col_lines.append(
            f"    {colname}: Mapped[{py_type_hint_field(f)}] = mapped_column({typ}, nullable={nullable}{default_expr}{comment})"
        )

    uc_lines = []
    if ent.unique_constraints:
        parts = []
        for name, cols in ent.unique_constraints:
            if cols:
                parts.append(f"UniqueConstraint({', '.join([repr(c) for c in cols])}, name={repr(name)})")
        if parts:
            uc_lines.append("    __table_args__ = (")
            for p in parts:
                uc_lines.append(f"        {p},")
            uc_lines.append("    )")

    content = []
    content.append(GEN_HEADER)
    content.append("from __future__ import annotations")
    content.append("")
    content.append("from datetime import datetime")
    content.append("from typing import Any, Dict, List, Optional")
    content.append("")
    # ✅ JSON 永远可 import，没坏处（简化生成逻辑）
    content.append("from sqlalchemy import Boolean, DateTime, Integer, BigInteger, String, Text, UniqueConstraint, JSON")
    content.append("from sqlalchemy.orm import Mapped, mapped_column")
    content.append("from sqlalchemy import Enum as SAEnum")
    content.append("")
    content.append(f"from {enums_module} import *")
    content.append(f"from {base_mod} import {base_name}")
    content.append(f"from {mixins_module} import " + ", ".join(sorted(set(mixins))))
    content.append("")
    content.append("")
    bases = ", ".join(mixins + [base_name])
    content.append(f"class {ent.class_name}({bases}):")
    if ent.comment:
        content.append(f'    """{py_str(ent.comment)}"""')
    content.append(f'    __tablename__ = "{py_str(ent.table_name)}"')
    if uc_lines:
        content.append("")
        content.extend(uc_lines)
    content.append("")
    content.extend(col_lines if col_lines else ["    pass"])
    content.append("")
    return "\n".join(content).rstrip() + "\n"


def render_schema_file(
    ent: EntityDef,
    enums_module: str,
    model_module: str,
    common_module: str,
) -> str:
    create_lines, update_lines, read_lines, query_lines = [], [], [], []
    for f in ent.fields:
        name = snake_case(f.name)
        hint = py_type_hint_field(f)
        if f.not_null:
            create_lines.append(f"    {name}: {hint}")
        else:
            create_lines.append(f"    {name}: Optional[{hint}] = None")
        update_lines.append(f"    {name}: Optional[{hint}] = None")
        read_lines.append(f"    {name}: Optional[{hint}] = None")
        query_lines.append(f"    {name}: Optional[{hint}] = None")

    content = []
    content.append(GEN_HEADER)
    content.append("from __future__ import annotations")
    content.append("")
    content.append("from datetime import datetime")
    # ✅ Json / List 类型会用到 Any/Dict/List
    content.append("from typing import Optional, Any, Dict, List")
    content.append("")
    content.append("from pydantic import BaseModel, ConfigDict")
    content.append("")
    content.append(f"from {enums_module} import *")
    content.append(f"from {model_module} import {ent.class_name}")
    content.append(f"from {common_module} import PageQuery, PageResult, BaseRead, IdsReq")
    content.append("")
    content.append("")
    content.append(f"class {ent.class_name}Create(BaseModel):")
    content.append("    model_config = ConfigDict(extra='forbid')")
    content.extend(create_lines or ["    pass"])
    content.append("")
    content.append(f"class {ent.class_name}Update(BaseModel):")
    content.append("    model_config = ConfigDict(extra='forbid')")
    content.append("    id: str")
    content.extend(update_lines or [])
    content.append("")
    content.append(f"class {ent.class_name}Query(PageQuery):")
    content.append("    model_config = ConfigDict(extra='forbid')")
    content.extend(query_lines or [])
    content.append("")
    content.append(f"class {ent.class_name}Read(BaseRead):")
    content.append("    model_config = ConfigDict(from_attributes=True)")
    content.extend(read_lines or [])
    content.append("")
    content.append(f"{ent.class_name}Page = PageResult[{ent.class_name}Read]")
    content.append("")
    return "\n".join(content).rstrip() + "\n"


def render_service_file(ent: EntityDef, service_base_module: str, model_module: str, stem: str) -> str:
    """
    ✅ Service 生成后自动尝试加载同目录下的 xxx_service_impl.py
       你的业务扩展逻辑放在 patch_service(ServiceClass) 里，不会被 codegen 覆盖
    """
    return textwrap.dedent(
        f"""
        {GEN_HEADER}
        from __future__ import annotations

        from {service_base_module} import CRUDService
        from {model_module} import {ent.class_name}


        class {ent.class_name}Service(CRUDService):
            model = {ent.class_name}


        # ✅ user extension hook (won't be overwritten)
        try:
            from .{stem}_service_impl import patch_service  # type: ignore
            patch_service({ent.class_name}Service)
        except Exception:
            pass
        """
    ).strip() + "\n"


def render_api_router_agg(imports: List[str], includes: List[str]) -> str:
    content = []
    content.append(GEN_HEADER)
    content.append("from __future__ import annotations")
    content.append("")
    content.append("from fastapi import APIRouter")
    content.append("")
    for imp in imports:
        content.append(imp)
    content.append("")
    content.append("api_router = APIRouter()")
    content.append("")
    for inc in includes:
        content.append(inc)
    content.append("")
    return "\n".join(content).rstrip() + "\n"


def render_api_file(
    ent: EntityDef,
    prefix: str,
    tags: List[str],
    schema_module: str,
    service_module: str,
    schema_common_module: str,
    deps_import: Tuple[str, List[str]],
    res_import: Tuple[str, str],
) -> str:
    deps_mod, deps_names = deps_import
    res_mod, res_name = res_import

    def has(name: str) -> bool:
        return name in (deps_names or [])

    # deps symbols（有就用，没有就降级）
    sym_get_db = "get_db" if has("get_db") else None
    sym_get_ctx = "get_ctx" if has("get_ctx") else None
    sym_get_ctx_required = "get_ctx_required" if has("get_ctx_required") else None
    sym_require_perm = "require_perm" if has("require_perm") else None
    sym_provide_service = "provide_service" if has("provide_service") else None
    sym_provide_service_optional = "provide_service_optional" if has("provide_service_optional") else None

    def needs_login(a: ApiDef) -> bool:
        # ✅ authRequired=true => 只要求登录
        # ✅ requiredPerms 非空 => 登录 + 权限
        return bool(a.auth_required) or bool(a.required_perms)

    def deps_import_line() -> str:
        need = []
        for x in [
            sym_get_db,
            sym_get_ctx,
            sym_get_ctx_required,
            sym_require_perm,
            sym_provide_service,
            sym_provide_service_optional,
        ]:
            if x and x not in need:
                need.append(x)
        return f"from {deps_mod} import " + ", ".join(need) if need else ""

    def build_dependencies(a: ApiDef) -> str:
        if not needs_login(a):
            return ""

        deps: List[str] = []
        # 登录依赖
        if sym_get_ctx_required:
            deps.append(f"Depends({sym_get_ctx_required})")
        elif sym_get_ctx:
            deps.append(f"Depends({sym_get_ctx})")

        # 权限依赖（仅 requiredPerms 生效）
        if sym_require_perm:
            for p in a.required_perms or []:
                deps.append(f"Depends({sym_require_perm}({p!r}))")

        if not deps:
            return ""
        return ", dependencies=[" + ", ".join(deps) + "]"

    def service_param(a: ApiDef) -> str:
        svc_cls = f"{ent.class_name}Service"

        # ✅ 需要登录 => 强制登录注入
        if needs_login(a) and sym_provide_service:
            return f"svc: {svc_cls} = Depends({sym_provide_service}({svc_cls}))"

        # ✅ 不需要登录 => 公开接口注入（允许匿名）
        if (not needs_login(a)) and sym_provide_service_optional:
            return f"svc: {svc_cls} = Depends({sym_provide_service_optional}({svc_cls}))"

        # fallback：不用 provider，就注入 db/ctx，自行 new service
        if sym_get_db and (sym_get_ctx_required if needs_login(a) else sym_get_ctx):
            ctx_sym = sym_get_ctx_required if needs_login(a) else sym_get_ctx
            return f"db=Depends({sym_get_db}), ctx=Depends({ctx_sym})"
        if sym_get_db:
            return f"db=Depends({sym_get_db})"
        return f"svc: {svc_cls} = None"

    def ensure_svc_lines(a: ApiDef) -> List[str]:
        """
        如果 service_param 走 fallback（db/ctx），这里补 svc = Service(db, ctx)
        """
        if "svc:" in service_param(a):
            return []
        return [f"    svc = {ent.class_name}Service(db, ctx)"]

    # ----------------------------
    # file header
    # ----------------------------
    content: List[str] = []
    content.append(GEN_HEADER)
    content.append("from __future__ import annotations")
    content.append("")
    content.append("from typing import Optional, Any, Dict, List")
    content.append("from datetime import datetime")
    content.append("")
    content.append("from fastapi import APIRouter, Depends, HTTPException")
    content.append("from pydantic import BaseModel, ConfigDict")
    content.append("")
    content.append(f"from {res_mod} import {res_name}")
    imp_line = deps_import_line()
    if imp_line:
        content.append(imp_line)
    content.append("")
    content.append(f"from {schema_module} import *")
    content.append(f"from {schema_common_module} import IdsReq")
    content.append(f"from {service_module} import {ent.class_name}Service")
    content.append("")
    content.append(f"router = APIRouter(prefix={prefix!r}, tags={tags!r})")
    content.append("")

    # ----------------------------
    # routes
    # ----------------------------
    for a in ent.apis:
        name = a.name
        path = a.path or f"/{name}"
        summary = a.summary or name
        dep_arg = build_dependencies(a)
        svc_arg = service_param(a)

        # CUSTOM：生成 DTO + endpoint
        if a.param_mode == "CUSTOM":
            dto = a.dto_name or f"{ent.class_name}{title_case(name)}Req"

            content.append(f"class {dto}(BaseModel):")
            content.append("    model_config = ConfigDict(extra='forbid')")
            if a.params:
                for p in a.params:
                    field_name = snake_case(p.name)
                    hint = py_type_hint_by_type(p.type, p.enum_name)
                    comment = py_str(p.comment or "")

                    if p.required:
                        content.append(f"    {field_name}: {hint}  # {comment}")
                    else:
                        content.append(f"    {field_name}: Optional[{hint}] = None  # {comment}")
            else:
                content.append("    pass")
            content.append("")

            content.append(f'@router.post("{path}", summary="{py_str(summary)}"{dep_arg})')
            content.append(f"def {name}(req: {dto}, {svc_arg}):")
            for ln in ensure_svc_lines(a):
                content.append(ln)
            content.append(f"    out = svc.{name}(req.model_dump())")
            content.append(f"    return {res_name}.success(out)")
            content.append("")
            continue

        # ENTITY save/update/list
        if a.param_mode == "ENTITY" and name == "save":
            content.append(f'@router.post("{path}", summary="{py_str(summary)}"{dep_arg})')
            content.append(f"def save(req: {ent.class_name}Create, {svc_arg}):")
            for ln in ensure_svc_lines(a):
                content.append(ln)
            content.append("    obj = svc.create(req.model_dump())")
            content.append(f"    return {res_name}.success({ent.class_name}Read.model_validate(obj))")
            content.append("")
            continue

        if a.param_mode == "ENTITY" and name == "update":
            content.append(f'@router.post("{path}", summary="{py_str(summary)}"{dep_arg})')
            content.append(f"def update(req: {ent.class_name}Update, {svc_arg}):")
            for ln in ensure_svc_lines(a):
                content.append(ln)
            content.append("    obj = svc.update(req.id, req.model_dump(exclude={'id'}))")
            content.append("    if not obj:")
            content.append("        raise HTTPException(status_code=404, detail='not found')")
            content.append(f"    return {res_name}.success({ent.class_name}Read.model_validate(obj))")
            content.append("")
            continue

        if a.param_mode == "ENTITY" and name == "list":
            content.append(f'@router.post("{path}", summary="{py_str(summary)}"{dep_arg})')
            content.append(f"def list_(req: {ent.class_name}Query, {svc_arg}):")
            for ln in ensure_svc_lines(a):
                content.append(ln)
            content.append("    filters = req.model_dump(exclude={'page','size','order_by'}, exclude_none=True)")
            content.append("    items = svc.list(filters, order_by=req.order_by)")
            content.append(f"    return {res_name}.success([{ent.class_name}Read.model_validate(x) for x in items])")
            content.append("")
            continue

        # IDS delete
        if a.param_mode == "IDS":
            content.append(f'@router.post("{path}", summary="{py_str(summary)}"{dep_arg})')
            content.append(f"def delete(req: IdsReq, {svc_arg}):")
            for ln in ensure_svc_lines(a):
                content.append(ln)
            content.append("    n = svc.delete_many(req.ids)")
            content.append(f"    return {res_name}.success({{'deleted': n}})")
            content.append("")
            continue

        # QUERY paging
        if a.param_mode == "QUERY":
            content.append(f'@router.post("{path}", summary="{py_str(summary)}"{dep_arg})')
            content.append(f"def paging(req: {ent.class_name}Query, {svc_arg}):")
            for ln in ensure_svc_lines(a):
                content.append(ln)
            content.append("    filters = req.model_dump(exclude={'page','size','order_by'}, exclude_none=True)")
            content.append("    total, items = svc.paging(filters, page=req.page, size=req.size, order_by=req.order_by)")
            content.append(f"    return {res_name}.success({{")
            content.append("        'total': total,")
            content.append(f"        'items': [{ent.class_name}Read.model_validate(x) for x in items],")
            content.append("    })")
            content.append("")
            continue

    return "\n".join(content).rstrip() + "\n"


# -------------------------
# Clean strategy (safe)
# -------------------------
def safe_clean(spec: Spec, app_dir: Path, cfg: CodegenConfig) -> None:
    enums_dir = app_dir / cfg.gen_paths["enums"]
    models_dir = app_dir / cfg.gen_paths["models"]
    schemas_dir = app_dir / cfg.gen_paths["schemas"]
    services_dir = app_dir / cfg.gen_paths["services"]
    api_dir = app_dir / cfg.gen_paths["api"]

    # 只删生成的公共文件（带 header 才删）
    gen_files = [
        enums_dir / "enums.py",
        models_dir / "_gen_mixins.py",
        schemas_dir / "_gen_common.py",
        services_dir / "_gen_base.py",
        api_dir / "router.py",  # ✅ 生成 router.py
    ]
    for f in gen_files:
        if is_generated_file(f):
            f.unlink()

    # 只删带 marker 的模块目录
    modules = sorted({e.module_name for e in spec.entities})
    for mod in modules:
        for root in [models_dir, schemas_dir, services_dir, api_dir]:
            d = root / mod
            if d.exists() and d.is_dir() and (d / DIR_MARKER).exists():
                shutil.rmtree(d)


# -------------------------
# Generate all
# -------------------------
def generate(spec: Spec, project_root: Path, cfg: CodegenConfig, clean: bool, spec_path: Path) -> None:
    app_dir = project_root / cfg.app_dir

    enums_dir = app_dir / cfg.gen_paths["enums"]
    models_dir = app_dir / cfg.gen_paths["models"]
    schemas_dir = app_dir / cfg.gen_paths["schemas"]
    services_dir = app_dir / cfg.gen_paths["services"]
    api_dir = app_dir / cfg.gen_paths["api"]

    # ensure packages
    ensure_init_py(enums_dir)
    ensure_init_py(models_dir)
    ensure_init_py(schemas_dir)
    ensure_init_py(services_dir)
    ensure_init_py(api_dir)

    if clean:
        safe_clean(spec, app_dir, cfg)

    # parse configurable imports
    base_mod, base_names = parse_import_target(cfg.imports["base"])
    if len(base_names) != 1:
        raise ValueError("imports.base must be module:SingleName")
    base_import = (base_mod, base_names[0])

    deps_mod, deps_names = parse_import_target(cfg.imports["deps"])
    deps_import = (deps_mod, deps_names)

    res_mod, res_names = parse_import_target(cfg.imports["res"])
    if len(res_names) != 1:
        raise ValueError("imports.res must be module:SingleName")
    res_import = (res_mod, res_names[0])

    # python package paths
    enums_pkg = f"{cfg.app_pkg}." + cfg.gen_paths["enums"].replace("/", ".")
    models_pkg = f"{cfg.app_pkg}." + cfg.gen_paths["models"].replace("/", ".")
    schemas_pkg = f"{cfg.app_pkg}." + cfg.gen_paths["schemas"].replace("/", ".")
    services_pkg = f"{cfg.app_pkg}." + cfg.gen_paths["services"].replace("/", ".")
    api_pkg = f"{cfg.app_pkg}." + cfg.gen_paths["api"].replace("/", ".")

    enums_module = f"{enums_pkg}.enums"
    mixins_module = f"{models_pkg}._gen_mixins"
    schema_common_module = f"{schemas_pkg}._gen_common"
    service_base_module = f"{services_pkg}._gen_base"

    # common files
    write_text(enums_dir / "enums.py", render_enums_file(spec))
    write_text(models_dir / "_gen_mixins.py", render_mixins_file())
    write_text(schemas_dir / "_gen_common.py", render_schema_common())
    write_text(services_dir / "_gen_base.py", render_service_base())

    api_imports: List[str] = []
    api_includes: List[str] = []

    for ent in spec.entities:
        mod = ent.module_name
        stem = guess_entity_file_stem(ent.class_name, ent.module_name)

        # module dirs
        mdir = models_dir / mod
        sdir = schemas_dir / mod
        svdir = services_dir / mod
        adir = api_dir / mod

        ensure_init_py(mdir)
        ensure_init_py(sdir)
        ensure_init_py(svdir)
        ensure_init_py(adir)

        # marker
        mark_codegen_dir(mdir, spec_path)
        mark_codegen_dir(sdir, spec_path)
        mark_codegen_dir(svdir, spec_path)
        mark_codegen_dir(adir, spec_path)

        model_module = f"{models_pkg}.{mod}.{stem}"
        schema_module = f"{schemas_pkg}.{mod}.{stem}"
        service_module = f"{services_pkg}.{mod}.{stem}_service"
        api_module = f"{api_pkg}.{mod}.{stem}"

        # write entity files
        write_text(
            mdir / f"{stem}.py",
            render_model_file(ent, enums_module, mixins_module, base_import),
        )
        write_text(
            sdir / f"{stem}.py",
            render_schema_file(ent, enums_module, model_module, schema_common_module),
        )
        write_text(
            svdir / f"{stem}_service.py",
            render_service_file(ent, service_base_module, model_module, stem),
        )

        # api file
        prefix = cfg.api_prefix_template.format(module=mod, entity=stem, className=ent.class_name)
        tag = cfg.api_tag_template.format(module=mod, entity=stem, className=ent.class_name)
        write_text(
            adir / f"{stem}.py",
            render_api_file(
                ent=ent,
                prefix=prefix,
                tags=[tag],
                schema_module=schema_module,
                service_module=service_module,
                schema_common_module=schema_common_module,
                deps_import=deps_import,
                res_import=res_import,
            ),
        )

        alias = f"{mod}_{stem}"
        api_imports.append(f"from {api_module} import router as {alias}_router")
        api_includes.append(f"api_router.include_router({alias}_router)")

    # ✅ 聚合路由：app/api/router.py
    write_text(api_dir / "router.py", render_api_router_agg(api_imports, api_includes))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="spec json path, e.g. specs/saas.spec.json")
    ap.add_argument("--config", default=None, help="codegen config json path, e.g. tools/codegen/codegen.config.json")
    ap.add_argument("--root", default=".", help="project root")
    ap.add_argument("--clean", action="store_true", help="clean generated modules/files only (SAFE)")
    args = ap.parse_args()

    spec_path = Path(args.spec).resolve()
    root = Path(args.root).resolve()
    cfg_path = Path(args.config).resolve() if args.config else None

    cfg = CodegenConfig.load(cfg_path)
    spec = load_spec(spec_path)
    generate(spec, root, cfg, clean=args.clean, spec_path=spec_path)

    print("✅ Codegen done.")
    print("Import api_router in app.main:")
    print("  from app.api.router import api_router")


if __name__ == "__main__":
    main()
