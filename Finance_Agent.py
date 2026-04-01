from __future__ import annotations

import json

from app.config import get_settings
from app.schemas import AnalyzeRequest
from app.services.analyzer import FinanceAnalyzer


def main() -> None:
    settings = get_settings()
    print("=== 欢迎使用 AI 金融助手（CLI 版）===")
    print(f"当前模型: {settings.ollama_model}")

    analyzer = FinanceAnalyzer()

    while True:
        target_code = input("\n请输入股票代码（如 600519.SH，输入 exit 退出）: ").strip()
        if target_code.lower() == "exit":
            print("已退出。")
            break

        try:
            request = AnalyzeRequest(stock_code=target_code, lookback_days=settings.default_lookback_days)
            result = analyzer.analyze(request)
            print("\n分析结果(JSON):")
            print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
        except Exception as exc:
            print(f"发生错误: {exc}")


if __name__ == "__main__":
    main()
