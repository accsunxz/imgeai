# app/services/agent/reddit_service.py
import os
import re
from typing import List, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

# LangChain & LangGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, START

# 你的项目依赖
from app.models.agent.reddit import RedditLog
from app.core.config import settings

# =========================================================
# A. 配置 DeepSeek-V3 (SiliconFlow)
# =========================================================

# 优先从 settings 读取，没有则读环境变量
API_KEY = getattr(settings, "SILICONFLOW_API_KEY", "") or os.getenv("SILICONFLOW_API_KEY")

if not API_KEY:
    # ⚠️ 实际运行时请确保已配置 Key
    print("Warning: SILICONFLOW_API_KEY not found.")

llm = ChatOpenAI(
    # 🔥 修正点：标准模型名称通常是这个
    model="deepseek-ai/DeepSeek-V3.2",
    openai_api_key=API_KEY,
    openai_api_base="https://api.siliconflow.cn/v1",
    # 🔥 温度设为 1.3，DeepSeek 官方推荐 V3 使用高温以增加创造力
    temperature=1.3,
    max_tokens=512,
    max_retries=2,
    model_kwargs={
        # 惩罚重复，防止废话
        "presence_penalty": 0.5,
        "frequency_penalty": 0.3,
        "top_p": 0.95,
    }
)

# =========================================================
# B. Prompt & 清洗逻辑 (去 AI 味核心)
# =========================================================

SYSTEM_PROMPT = """You are a cynical, tired Reddit user posting from your phone. 
You are NOT an AI. You hate corporate buzzwords.

**HARD RULES (Do NOT break):**
1. NO BUZZWORDS: Never use 'unleash', 'elevate', 'seamless', 'game-changer', 'tapestry', 'delve'.
2. NO FORMATTING: Do NOT use bullet points, bold headers, or lists. Write in messy paragraphs.
3. NO GREETINGS: Do NOT start with "Hey guys". Just start venting.
4. LOWERCASE VIBE: Use mostly lowercase. It looks more real.
5. BE SPECIFIC: Make up small details (e.g., "tried for 2 weeks", "cost $50") if the input is vague.

Your task: Rewrite the Chinese input into a casual, short, authentic English Reddit post.
"""

FEW_SHOT_EXAMPLES = """
Examples:

Input: 我们开发了一个新工具，可以帮助大家提高效率，现在的困难是不知道怎么推广。
Output: built a small automation tool for my own workflow. works great but i have zero clue how to get first users without being spammy. marketing feels like a black box lol.

Input: 大家觉得远程工作怎么样？虽然很自由，但是有时候感觉很孤独，效率也不高。
Output: honestly struggling with wfh. the freedom is nice i guess, but the isolation is getting to me. find myself staring at the wall instead of working half the time. anyone else hit this wall?

Input: 我们的加班费制度很混乱，员工很不满。
Output: trying to fix our overtime rules and it's a nightmare. whenever work spikes we just throw OT at it, but now the budget is blown and the team is burnt out. how do you guys handle this without making everyone hate you?
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{few_shot}\n\nInput: {input_text}\nOutput:")
])

chain = prompt_template | llm


def post_clean(text: str) -> str:
    """暴力清洗：去掉 AI 常见的“客套话”和“格式化痕迹”"""
    s = (text or "").strip()
    # 去引号
    s = s.strip('"').strip("'")
    # 去 AI 开场白 (DeepSeek 偶尔会比较礼貌)
    s = re.sub(r"^(Here is|Sure,|Here's|Okay,).+?:\s*", "", s, flags=re.IGNORECASE)
    # 强制首字母小写 (Reddit 风格)
    if len(s) > 0 and s[0].isupper():
        s = s[0].lower() + s[1:]
    # 去 Hashtag
    s = re.sub(r"#\w+", "", s)
    return s.strip()


# =========================================================
# C. LangGraph 定义
# =========================================================

class AgentState(TypedDict):
    input_text: str
    final_output: str


async def generate_node(state: AgentState):
    response = await chain.ainvoke({
        "few_shot": FEW_SHOT_EXAMPLES,
        "input_text": state["input_text"]
    })
    return {"final_output": post_clean(response.content)}


workflow = StateGraph(AgentState)
workflow.add_node("generate", generate_node)
workflow.add_edge(START, "generate")
workflow.add_edge("generate", END)
app_graph = workflow.compile()


# =========================================================
# D. Service 类 (供 Router 调用)
# =========================================================

class RedditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def translate(self, text: str):
        # 1. 记录入库 (PENDING)
        log = RedditLog(input_text=text, status="PENDING")
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        try:
            # 2. 调用 AI
            result = await app_graph.ainvoke({"input_text": text})
            output = result["final_output"]

            # 3. 更新结果 (DONE)
            log.output_text = output
            log.style_refs = ["DeepSeek-V3", "Few-Shot"]  # 标记使用的策略
            log.status = "DONE"
            await self.db.commit()

            # 4. 返回符合 Pydantic Schema 的 dict
            return {
                "id": str(log.id),
                "input_text": log.input_text,
                "output_text": log.output_text,
                "style_refs": log.style_refs,
                "status": log.status
            }

        except Exception as e:
            await self.db.rollback()
            # 标记为错误
            log.status = "ERROR"
            # 注意：rollback 后 log 对象会从 session 中 detach，需要重新 add
            self.db.add(log)
            await self.db.commit()
            raise e

    async def get_history(self, limit: int = 10):
        stmt = select(RedditLog).order_by(desc(RedditLog.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        # 转换为 Schema 格式
        return [
            {
                "id": str(log.id),
                "input_text": log.input_text,
                "output_text": log.output_text,
                "style_refs": log.style_refs,
                "status": log.status
            }
            for log in logs
        ]