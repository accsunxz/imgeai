import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 1. 必须先运行这一行，才能把 .env 里的变量注入到系统环境
load_dotenv()

# 2. 从环境变量读取你的 Key
# 注意：确保变量名与 .env 文件中 sk-xxxx 前面的那个名字完全一模一样
api_key = os.getenv("SILICONFLOW_API_KEY")

# 3. 增加一个简单的断言，如果没读到 Key，直接报错提醒，而不是让 LangChain 崩溃
if not api_key:
    raise ValueError("❌ 错误：环境变量 SILICONFLOW_API_KEY 为空，请检查 .env 文件内容和路径！")

# 4. 初始化 LLM
llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",
    openai_api_key=api_key, # 这里必须确保传入的是有效的字符串
    openai_api_base="https://api.siliconflow.cn/v1",
    max_tokens=1024
)