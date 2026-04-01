from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

# Matplotlib 默认会在用户目录写缓存，这里强制改到可写临时目录，避免权限问题。
mpl_cache_dir = Path(tempfile.gettempdir()) / "finance_agent_mplcache"
mpl_cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(mpl_cache_dir))

import matplotlib

matplotlib.use("Agg")
import mplfinance as mpf
import pandas as pd

from app.config import get_settings


class ChartService:
    def __init__(self) -> None:
        settings = get_settings()
        self.output_dir = Path(settings.chart_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_candlestick(self, df: pd.DataFrame, stock_code: str, stock_name: str) -> tuple[str, str]:
        if df.empty:
            raise ValueError("数据为空，无法绘制 K 线图")

        chart_df = df.copy()
        chart_df["trade_date"] = pd.to_datetime(chart_df["trade_date"], format="%Y%m%d")
        chart_df = chart_df.set_index("trade_date").sort_index()

        plot_df = chart_df[["open", "high", "low", "close", "vol"]].copy()
        plot_df.columns = ["Open", "High", "Low", "Close", "Volume"]

        style = mpf.make_mpf_style(
            base_mpf_style="charles",
            rc={"font.family": "Arial Unicode MS", "axes.unicode_minus": False},
        )

        end_date = plot_df.index[-1].strftime("%Y%m%d")
        ts = datetime.now().strftime("%H%M%S")
        safe_code = re.sub(r"[^A-Za-z0-9_.-]", "_", stock_code)
        file_name = f"{safe_code}_{end_date}_{ts}.png"
        file_path = self.output_dir / file_name

        mpf.plot(
            plot_df,
            type="candle",
            style=style,
            title=f"{stock_name} ({stock_code}) 近期 K 线图",
            ylabel="价格 (元)",
            ylabel_lower="成交量",
            volume=True,
            mav=(5, 10),
            figratio=(12, 8),
            show_nontrading=False,
            savefig=dict(fname=str(file_path), dpi=160, bbox_inches="tight"),
        )

        return file_name, str(file_path)
