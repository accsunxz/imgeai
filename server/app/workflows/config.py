# config.py
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./reddit_translation.db"

    # SiliconFlow 配置
    # 优先从环境变量读取，如果读不到，则使用默认值 (请替换为你的真实 Key)
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY")
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"

    # 推荐使用 DeepSeek-V3
    SILICONFLOW_MODEL: str = "deepseek-ai/DeepSeek-V3.2"

    class Config:
        env_file = ".env"


settings = Settings()