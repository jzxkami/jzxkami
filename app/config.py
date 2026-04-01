from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    tushare_token: str
    ollama_model: str
    ollama_host: str
    default_lookback_days: int
    max_rows_for_prompt: int
    llm_temperature: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        tushare_token=os.getenv("TUSHARE_TOKEN", "").strip(),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3").strip() or "llama3",
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").strip() or "http://localhost:11434",
        default_lookback_days=int(os.getenv("DEFAULT_LOOKBACK_DAYS", "20")),
        max_rows_for_prompt=int(os.getenv("MAX_ROWS_FOR_PROMPT", "20")),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
    )
