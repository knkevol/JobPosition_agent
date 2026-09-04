# BaseSetting 상속 시 .env 파일 값을 읽어 자동으로 타입검증하는 설정 객체 생성 가능
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str = ""
    github_token: str = ""
    app_env:str = "local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Setting값을 프로그램 전체에서 한번만 읽어서 재사용하기 위한 캐시 장치
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()