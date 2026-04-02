from __future__ import annotations

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalyzeRequest(BaseModel):
    stock_code: str = Field(..., description="股票代码，例如 600519.SH")
    stock_name: str | None = Field(default=None, description="股票名称，可选，不传则自动查询")
    lookback_days: int = Field(default=20, ge=5, le=120, description="使用最近 N 个交易日")
    include_news: bool = Field(default=False, description="是否启用新闻增强（RAG）")
    include_chart: bool = Field(default=True, description="是否生成 K 线图")
    news_lookback_hours: int | None = Field(
        default=None,
        ge=6,
        le=720,
        description="新闻检索时间窗（小时），仅 include_news=true 时生效",
    )
    news_top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="注入模型的新闻条数，仅 include_news=true 时生效",
    )
    news_fetch_limit: int | None = Field(
        default=None,
        ge=20,
        le=500,
        description="单次新闻接口最大拉取条数，仅 include_news=true 时生效",
    )

    @field_validator("stock_code")
    @classmethod
    def validate_stock_code(cls, value: str) -> str:
        code = value.strip().upper()
        if not re.match(r"^\d{6}\.(SH|SZ|BJ)$", code):
            raise ValueError("stock_code 格式应为 600519.SH / 000001.SZ / 430047.BJ")
        return code


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, description="用户名（3-32位，字母/数字/下划线）")
    password: str = Field(..., min_length=6, max_length=128, description="登录密码")


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)


class UserProfile(BaseModel):
    user_id: int
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    user: UserProfile


class LogoutResponse(BaseModel):
    success: bool = True


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


class NewsEvidence(BaseModel):
    title: str
    pub_time: str
    source: str
    url: str | None = None
    snippet: str | None = None
    relevance: float | None = None


class NewsDebug(BaseModel):
    requested: bool
    effective_lookback_hours: int | None = None
    effective_top_k: int | None = None
    effective_fetch_limit: int | None = None
    major_count: int = 0
    news_count: int = 0
    selected_count: int = 0
    cache_hit: bool | None = None
    stale_fallback_used: bool | None = None


class CacheInfo(BaseModel):
    daily_hit: bool
    stock_name_hit: bool
    news_hit: bool | None = None
    news_stale_fallback_used: bool | None = None
    daily_hits_total: int
    daily_misses_total: int
    stock_name_hits_total: int
    stock_name_misses_total: int
    news_hits_total: int | None = None
    news_misses_total: int | None = None


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
    news_items: list[NewsEvidence] = Field(default_factory=list)
    news_debug: NewsDebug | None = None
    warnings: list[str] = Field(default_factory=list)
