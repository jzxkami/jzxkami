from __future__ import annotations

import datetime as dt

import pandas as pd
import tushare as ts

from app.config import get_settings
from app.schemas import PriceSummary


class MarketDataService:
    def __init__(self) -> None:
        self._pro = None

    def _ensure_client(self):
        settings = get_settings()
        if not settings.tushare_token:
            raise RuntimeError("未读取到 TUSHARE_TOKEN，请在 .env 或环境变量中配置后重试")

        if self._pro is None:
            ts.set_token(settings.tushare_token)
            self._pro = ts.pro_api()
        return self._pro

    def fetch_recent_daily(self, stock_code: str, lookback_days: int) -> pd.DataFrame:
        pro = self._ensure_client()

        end_date = dt.date.today()
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

        return df

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
