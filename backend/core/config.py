from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False, extra='ignore')
    llm_provider: str = 'ollama'
    ollama_base_url: str = 'http://localhost:11434'
    ollama_model: str = 'qwen3:8b'
    api_host: str = '0.0.0.0'
    api_port: int = 8002
    streamlit_api_base_url: str = 'http://localhost:8002'
    max_sources: int = 6
    request_timeout_seconds: int = 12
    report_dir: str = 'data/reports'

    @property
    def report_path(self) -> Path:
        p = Path(self.report_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
