from __future__ import annotations

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalyzeRequest(BaseModel):
    stock_code: str = Field(..., description="股票代码，例如 600519.SH")
    stock_name: str | None = Field(default=None, description="股票名称，可选，不传则自动查询")
    lookback_days: int = Field(default=20, ge=5, le=120, description="使用最近 N 个交易日")
    include_news: bool = Field(default=False, description="是否启用新闻增强（RAG 预留位）")
    include_chart: bool = Field(default=True, description="是否生成 K 线图")

    @field_validator("stock_code")
    @classmethod
    def validate_stock_code(cls, value: str) -> str:
        code = value.strip().upper()
        if not re.match(r"^\d{6}\.(SH|SZ|BJ)$", code):
            raise ValueError("stock_code 格式应为 600519.SH / 000001.SZ / 430047.BJ")
        return code


class PriceSummary(BaseModel):
    start_date: date
    end_date: date
    latest_close: float
    period_change_pct: float
    high: float
    low: float
    high_low_spread: float
    high_low_spread_pct: float
    avg_volume: float
    trend: Literal["up", "down", "sideways"]


class AIInsight(BaseModel):
    trend: Literal["up", "down", "sideways"]
    reason: str
    volatility: str
    advice: str
    risk_level: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)


class CacheInfo(BaseModel):
    daily_hit: bool
    stock_name_hit: bool
    daily_hits_total: int
    daily_misses_total: int
    stock_name_hits_total: int
    stock_name_misses_total: int


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    stock_code: str
    stock_name: str
    generated_at: datetime
    price_summary: PriceSummary
    ai_insight: AIInsight
    chart_url: str | None = None
    chart_file: str | None = None
    cache_info: CacheInfo | None = None
    used_news_items: int = 0
    warnings: list[str] = Field(default_factory=list)
