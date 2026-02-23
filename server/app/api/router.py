# generated - DO NOT EDIT
from __future__ import annotations

from fastapi import APIRouter



from app.api.agent.style_transfer_router import router as style_transfer_router

api_router = APIRouter()


api_router.include_router(style_transfer_router)
