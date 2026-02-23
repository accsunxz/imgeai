from fastapi import APIRouter
from pydantic import BaseModel
from app.common.res import Res  # 假设你的 Res 类在这里
from app.services.agent.style_transfer_service import StyleTransferService
from app.workflows.scenario_manager import scenario_manager

router = APIRouter(prefix="/agent", tags=["AI Agent"])

class TransferRequest(BaseModel):
    text: str
    scene_id: str
    intent_id: str
    tone_id: str

@router.post("/translate")
async def translate_text(req: TransferRequest):
    svc = StyleTransferService(db=None)
    result = await svc.translate(
        text=req.text,
        scene_id=req.scene_id,
        intent_id=req.intent_id,
        tone_id=req.tone_id
    )
    # 使用 Res.success 包装，数据放入 body 字段
    return Res.success(body=result)

@router.get("/scenarios")
async def get_scenarios():
    """
    前端通过此接口获取 Scene -> Intent -> Tone 的完整树状结构
    """
    # 严格遵守 Res 结构，将场景列表放入 body
    return Res.success(body=scenario_manager.scenes)