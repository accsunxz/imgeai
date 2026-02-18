from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = Field(default="imgeai-server", alias="APP_NAME")
    database_url: str = Field(default="sqlite+aiosqlite:///./app.db", alias="DATABASE_URL")


    jwt_secret_key: str = Field(default="change_me_to_a_long_random_string", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=120, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    SILICONFLOW_API_KEY: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
