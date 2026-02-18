# generated - DO NOT EDIT
from __future__ import annotations

from fastapi import APIRouter



from app.api.agent.reddit import router as agent_reddit_router

api_router = APIRouter()


api_router.include_router(agent_reddit_router)
