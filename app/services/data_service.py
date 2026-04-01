from __future__ import annotations

import datetime as dt
from typing import Any

import pandas as pd
import tushare as ts

from app.config import get_settings
from app.schemas import PriceSummary
from app.services.ttl_cache import TTLCache


class MarketDataService:
    def __init__(self) -> None:
        self._pro = None
        settings = get_settings()

        self._daily_cache: TTLCache[tuple[str, int, str], pd.DataFrame] = TTLCache(
            ttl_seconds=settings.daily_cache_ttl_seconds,
            maxsize=settings.daily_cache_maxsize,
        )
        self._stock_name_cache: TTLCache[str, str] = TTLCache(
            ttl_seconds=settings.stock_name_cache_ttl_seconds,
            maxsize=settings.stock_name_cache_maxsize,
        )

    def _ensure_client(self):
        settings = get_settings()
        if not settings.tushare_token:
            raise RuntimeError("未读取到 TUSHARE_TOKEN，请在 .env 或环境变量中配置后重试")

        if self._pro is None:
            # 直接传 token，避免 set_token 写入用户目录文件（tk.csv）引发权限问题。
            self._pro = ts.pro_api(settings.tushare_token)
        return self._pro

    def resolve_stock_name_with_cache(self, stock_code: str) -> tuple[str, bool]:
        hit, cached_name = self._stock_name_cache.get(stock_code)
        if hit and cached_name:
            return cached_name, True

        resolved = stock_code
        try:
            pro = self._ensure_client()
            df = pro.stock_basic(ts_code=stock_code, fields="ts_code,name")
            if df is not None and not df.empty and "name" in df.columns:
                resolved = str(df.iloc[0]["name"]) or stock_code
        except Exception:
            resolved = stock_code

        self._stock_name_cache.set(stock_code, resolved)
        return resolved, False

    def resolve_stock_name(self, stock_code: str) -> str:
        name, _ = self.resolve_stock_name_with_cache(stock_code)
        return name

    def fetch_recent_daily_with_cache(self, stock_code: str, lookback_days: int) -> tuple[pd.DataFrame, bool]:
        end_date = dt.date.today()
        cache_key = (stock_code, lookback_days, end_date.strftime("%Y%m%d"))

        hit, cached_df = self._daily_cache.get(cache_key)
        if hit and cached_df is not None:
            return cached_df.copy(deep=True), True

        pro = self._ensure_client()
        start_date = end_date - dt.timedelta(days=max(lookback_days * 3, 30))

        df = pro.daily(
            ts_code=stock_code,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
        )

        if df is None or df.empty:
            raise ValueError(f"未查到 {stock_code} 的日线数据，请检查代码后重试")

        df = df.sort_values("trade_date").reset_index(drop=True)
        if len(df) > lookback_days:
            df = df.tail(lookback_days).reset_index(drop=True)

        self._daily_cache.set(cache_key, df)
        return df.copy(deep=True), False

    def fetch_recent_daily(self, stock_code: str, lookback_days: int) -> pd.DataFrame:
        df, _ = self.fetch_recent_daily_with_cache(stock_code, lookback_days)
        return df

    def get_cache_stats(self) -> dict[str, Any]:
        return {
            "daily": self._daily_cache.stats(),
            "stock_name": self._stock_name_cache.stats(),
        }

    @staticmethod
    def build_price_summary(df: pd.DataFrame) -> PriceSummary:
        if df.empty:
            raise ValueError("数据为空，无法生成价格摘要")

        start_close = float(df["close"].iloc[0])
        latest_close = float(df["close"].iloc[-1])
        period_change_pct = ((latest_close - start_close) / start_close * 100) if start_close else 0.0

        high = float(df["high"].max())
        low = float(df["low"].min())
        spread = high - low
        spread_pct = (spread / low * 100) if low else 0.0

        trend: str
        if period_change_pct > 1:
            trend = "up"
        elif period_change_pct < -1:
            trend = "down"
        else:
            trend = "sideways"

        start_date = pd.to_datetime(df["trade_date"].iloc[0], format="%Y%m%d").date()
        end_date = pd.to_datetime(df["trade_date"].iloc[-1], format="%Y%m%d").date()

        return PriceSummary(
            start_date=start_date,
            end_date=end_date,
            latest_close=round(latest_close, 4),
            period_change_pct=round(period_change_pct, 4),
            high=round(high, 4),
            low=round(low, 4),
            high_low_spread=round(spread, 4),
            high_low_spread_pct=round(spread_pct, 4),
            avg_volume=round(float(df["vol"].mean()), 4),
            trend=trend,
        )

    @staticmethod
    def build_prompt_rows(df: pd.DataFrame, max_rows: int) -> list[dict]:
        columns = ["trade_date", "open", "high", "low", "close", "vol", "pct_chg"]
        existing_cols = [col for col in columns if col in df.columns]
        prompt_df = df[existing_cols].copy().tail(max_rows)
        prompt_df["trade_date"] = prompt_df["trade_date"].astype(str)
        return prompt_df.to_dict(orient="records")
