# app/api/endpoints/reddit.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

# 引入你的 DB 依赖
from app.deps import get_db # 假设你的 get_db 在 app.deps 里，或者 app.core.database
from app.services.agent.reddit_service import RedditService

router = APIRouter()

# --- Schemas ---
class TranslateReq(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str

class TranslateRes(BaseModel):
    id: str
    input_text: str
    output_text: Optional[str]
    style_refs: Optional[List[str]]
    status: str

# --- Endpoints ---

@router.post("/translate", response_model=TranslateRes, summary="Reddit 风格生成")
async def translate(
    req: TranslateReq,
    db: AsyncSession = Depends(get_db)
):
    print(req)
    svc = RedditService(db)
    return await svc.translate(req.text)

@router.get("/history", response_model=List[TranslateRes], summary="生成历史")
async def history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    svc = RedditService(db)
    return await svc.get_history(limit)