# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import init_db, engine
from app.core.exception_handlers import register_exception_handlers
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ 修改：加上 await
    await init_db()
    print("✅ Database initialized (Async)")

    yield

    # ✅ 修改：加上 await
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router)
register_exception_handlers(app)

