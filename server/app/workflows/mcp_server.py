import json
from fastmcp import FastMCP
from app.workflows.scenario_manager import scenario_manager
from app.workflows.retriever import retriever

# -------------------------------------------------------------------------
# MCP 服务端 (Model Context Protocol Server)
# 核心职责：作为能力提供方，将本地的读取、检索、组装能力封装为标准 JSON-RPC 接口。
# 解耦后，任意支持 MCP 的客户端（LangGraph / Cursor）均可通过协议调用这些能力。
# -------------------------------------------------------------------------

mcp = FastMCP("Style-Transfer-Server")

@mcp.resource("config://scenarios")
def get_scenarios_config() -> str:
    """提供只读的场景配置资源"""
    return json.dumps(scenario_manager.scenes, ensure_ascii=False)

@mcp.tool()
async def fetch_reddit_context(scene_id: str, intent_id: str) -> str:
    """提供可执行工具：调用底层 RAG 获取上下文"""
    return await retriever.get_dynamic_examples(scene_id, intent_id)

@mcp.tool()
def build_prompt_template(scene_id: str, intent_id: str, tone_id: str) -> str:
    """提供可执行工具：组装并返回提示词的系统与人类部分"""
    template = scenario_manager.get_prompt_template(scene_id, intent_id, tone_id)
    result = {
        "system": template.messages[0].prompt.template,
        "human": template.messages[1].prompt.template
    }
    return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()