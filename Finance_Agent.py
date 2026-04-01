from __future__ import annotations

import webbrowser
from pathlib import Path

from app.config import get_settings
from app.services.ai_service import AIService
from app.services.chart_service import ChartService
from app.services.data_service import MarketDataService


def try_open_chart(chart_path: Path) -> None:
    try:
        webbrowser.open(chart_path.resolve().as_uri())
    except Exception:
        pass


def main() -> None:
    settings = get_settings()
    data_service = MarketDataService()
    chart_service = ChartService()
    ai_service = AIService()

    print("=== 🤖 欢迎使用你的个人 AI 金融助手 ===")

    while True:
        target_code = input("\n请输入股票代码（如 600519.SH，输入 exit 退出）: ").strip().upper()

        if target_code.lower() == "exit":
            print("👋 再见，祝你投资顺利！")
            break

        try:
            print(f"📡 正在调取 {target_code} 真实市场数据...")
            df = data_service.fetch_recent_daily(target_code, settings.default_lookback_days)
            stock_name = data_service.resolve_stock_name(target_code)

            print(f"📊 正在生成 {target_code} 专业 K 线图...")
            chart_file, chart_path = chart_service.render_candlestick(df, target_code, stock_name)
            try_open_chart(Path(chart_path))

            price_summary = data_service.build_price_summary(df)
            rows = data_service.build_prompt_rows(df, settings.max_rows_for_prompt)

            print("🧠 AI 正在根据图表数据进行深度分析...")
            insight = ai_service.analyze(
                stock_code=target_code,
                stock_name=stock_name,
                price_summary=price_summary,
                rows=rows,
                news_items=[],
            )

            print("\n" + "=" * 30)
            print(f"📊 {stock_name} ({target_code}) 分析报告：")
            print(f"1. 【价格趋势】：{insight.trend}。{insight.reason}")
            print(f"2. 【波动情况】：{insight.volatility}")
            print(f"3. 【投资建议】：{insight.advice}")
            print(f"4. 【风险等级】：{insight.risk_level}（置信度 {insight.confidence:.2f}）")
            print(f"5. 【K线图文件】：{chart_file}")
            print("=" * 30)

        except Exception as exc:
            print(f"⚠️ 发生错误: {exc}")


if __name__ == "__main__":
    main()
