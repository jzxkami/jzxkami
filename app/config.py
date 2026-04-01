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
    chart_output_dir: str
    daily_cache_ttl_seconds: int
    daily_cache_maxsize: int
    stock_name_cache_ttl_seconds: int
    stock_name_cache_maxsize: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        tushare_token=os.getenv("TUSHARE_TOKEN", "").strip(),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3").strip() or "llama3",
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").strip() or "http://localhost:11434",
        default_lookback_days=int(os.getenv("DEFAULT_LOOKBACK_DAYS", "20")),
        max_rows_for_prompt=int(os.getenv("MAX_ROWS_FOR_PROMPT", "20")),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        chart_output_dir=os.getenv("CHART_OUTPUT_DIR", "outputs/charts").strip() or "outputs/charts",
        daily_cache_ttl_seconds=int(os.getenv("DAILY_CACHE_TTL_SECONDS", "43200")),
        daily_cache_maxsize=int(os.getenv("DAILY_CACHE_MAXSIZE", "256")),
        stock_name_cache_ttl_seconds=int(os.getenv("STOCK_NAME_CACHE_TTL_SECONDS", "86400")),
        stock_name_cache_maxsize=int(os.getenv("STOCK_NAME_CACHE_MAXSIZE", "1024")),
    )
