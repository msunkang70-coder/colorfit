from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost:5432/colorfit"
    naver_client_id: str = ""
    naver_client_secret: str = ""
    gemini_api_key: str = ""
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://frontend-msunkang70-1055s-projects.vercel.app",
        "https://frontend-three-phi-i54lja481t.vercel.app",
    ]
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
