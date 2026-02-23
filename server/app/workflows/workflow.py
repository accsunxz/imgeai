import json
from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.workflows.config import llm
from app.workflows.scenario_manager import scenario_manager

class AgentState(TypedDict):
    scene_id: str
    intent_id: str
    tone_id: str
    input_text: str
    few_shot_context: str
    final_output: dict

# 配置 MCP 客户端，通过 stdio 协议启动服务进程
MCP_SERVERS = {
    "style_server": {
        "command": "python",
        "args": ["-m", "app.workflows.mcp_server"],
        "transport": "stdio"
    }
}

def extract_mcp_text(response) -> str:
    """提取 MCP 标准响应中的文本内容"""
    if hasattr(response, 'content') and isinstance(response.content, list):
        return "".join(item.text for item in response.content if hasattr(item, 'text'))
    return str(response)

async def analyze_node(state: AgentState):
    return {
        "scene_id": state.get("scene_id", "reddit"),
        "intent_id": state.get("intent_id", "venting"),
        "tone_id": state.get("tone_id", "sarcastic")
    }

async def retrieve_node(state: AgentState):
    """【修复点1】通过 session 调用工具"""
    client = MultiServerMCPClient(MCP_SERVERS)

    # 使用新版 API: 开启指定 server 的 session
    async with client.session("style_server") as session:
        # 使用 session.call_tool 替代 client.invoke_tool，参数名改为 arguments
        response = await session.call_tool(
            "fetch_reddit_context",
            arguments={"scene_id": state["scene_id"], "intent_id": state["intent_id"]}
        )
        context = extract_mcp_text(response)

    return {"few_shot_context": context}

async def generate_node(state: AgentState):
    """【修复点2】通过 session 调用工具获取 Prompt，并调度大模型生成结果"""
    s_id, i_id, t_id = state["scene_id"], state["intent_id"], state["tone_id"]

    # 1. IPC 通信获取提示词
    client = MultiServerMCPClient(MCP_SERVERS)
    async with client.session("style_server") as session:
        response = await session.call_tool(
            "build_prompt_template",
            arguments={"scene_id": s_id, "intent_id": i_id, "tone_id": t_id}
        )
        prompt_data_str = extract_mcp_text(response)
        prompts = json.loads(prompt_data_str)

    # 2. 动态重组 LangChain Prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts["system"]),
        ("human", prompts["human"])
    ])

    # 3. 绑定参数并执行大模型调用
    tone_config = scenario_manager.get_tone(s_id, i_id, t_id)
    bound_llm = llm.bind(**tone_config.get("llm_params", {}))
    chain = prompt_template | bound_llm | JsonOutputParser()

    result = await chain.ainvoke({
        "few_shot_context": state.get("few_shot_context", ""),
        "input_text": state["input_text"]
    })

    if "english" in result:
        result["english"] = scenario_manager.post_clean(result["english"])

    return {"final_output": result}

def route_by_rag(state: AgentState):
    cfg = scenario_manager.get_rag_config(state["scene_id"], state["intent_id"])
    return "retrieve" if cfg.get("enabled", False) else "generate"

# 构建图结构
builder = StateGraph(AgentState)
builder.add_node("analyze", analyze_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)

builder.add_edge(START, "analyze")
builder.add_conditional_edges("analyze", route_by_rag, {"retrieve": "retrieve", "generate": "generate"})
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

app_graph = builder.compile()