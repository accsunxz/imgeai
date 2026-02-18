# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.models.base import Base

# ✅ 关键修正：必须在这里显式导入你的模型，否则 create_all 不会创建这张表！
from app.models.agent.reddit import RedditLog
# 如果还有 SysUser，也要导入: from app.models.sys.user import SysUser

is_sqlite = "sqlite" in settings.database_url

engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False, # 开发时可以设为 True 开启 SQL 日志
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update(
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
    )

# 1. 创建异步引擎
engine = create_async_engine(settings.database_url, **engine_kwargs)

# 2. 创建异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False # 异步开发建议设为 False
)

# 3. 异步 get_db 依赖
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# 4. 异步建表函数
async def init_db() -> None:
    async with engine.begin() as conn:
        # run_sync 允许我们在异步连接中运行同步的 create_all
        await conn.run_sync(Base.metadata.create_all)