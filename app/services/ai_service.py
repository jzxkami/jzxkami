from __future__ import annotations

import json
import re

import ollama

from app.config import get_settings
from app.schemas import AIInsight, PriceSummary


class AIService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.ollama_model
        self.temperature = settings.llm_temperature
        self.client = ollama.Client(host=settings.ollama_host)

    def analyze(
        self,
        stock_code: str,
        stock_name: str,
        price_summary: PriceSummary,
        rows: list[dict],
        news_items: list[str],
    ) -> AIInsight:
        prompt = self._build_prompt(stock_code, stock_name, price_summary, rows, news_items)

        raw = ""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                format="json",
                options={"temperature": self.temperature},
            )
            raw = (response.get("response") or "").strip()
            if not raw:
                raise ValueError("模型返回为空")

            parsed = self._parse_json(raw)
            return AIInsight.model_validate(parsed)
        except Exception:
            # Fail-safe fallback: keep API always structured and parsable.
            return self._fallback(price_summary)

    @staticmethod
    def _parse_json(text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("未找到 JSON 对象")

        return json.loads(match.group(0))

    @staticmethod
    def _build_prompt(
        stock_code: str,
        stock_name: str,
        price_summary: PriceSummary,
        rows: list[dict],
        news_items: list[str],
    ) -> str:
        news_text = "\n".join(f"- {item}" for item in news_items) if news_items else "- 无"

        return f"""
你是专业中文金融分析师。你的任务是输出结构化 JSON。

股票代码: {stock_code}
股票名称: {stock_name}

价格摘要:
- 区间: {price_summary.start_date} ~ {price_summary.end_date}
- 最新收盘价: {price_summary.latest_close}
- 区间涨跌幅(%): {price_summary.period_change_pct}
- 最高价: {price_summary.high}
- 最低价: {price_summary.low}
- 振幅价差: {price_summary.high_low_spread}
- 振幅百分比(%): {price_summary.high_low_spread_pct}
- 平均成交量: {price_summary.avg_volume}

最近交易日明细(JSON数组):
{json.dumps(rows, ensure_ascii=False)}

新闻上下文:
{news_text}

请仅返回严格 JSON，不要输出 markdown，不要附加解释。字段必须完整:
{{
  "trend": "up|down|sideways",
  "reason": "一句或两句中文原因",
  "volatility": "对波动风险的中文描述",
  "advice": "一句中文建议（非投资承诺）",
  "risk_level": "low|medium|high",
  "confidence": 0.0
}}
""".strip()

    @staticmethod
    def _fallback(price_summary: PriceSummary) -> AIInsight:
        risk_level = "high" if price_summary.high_low_spread_pct > 10 else "medium"
        if abs(price_summary.period_change_pct) < 1.5 and price_summary.high_low_spread_pct < 6:
            risk_level = "low"

        advice = "可继续观察量价配合，避免追涨杀跌。"
        if risk_level == "high":
            advice = "波动较大，建议控制仓位并设置风险边界。"

        return AIInsight(
            trend=price_summary.trend,
            reason="模型输出异常，已使用规则引擎兜底。趋势依据区间涨跌幅计算。",
            volatility=f"区间振幅约 {price_summary.high_low_spread_pct:.2f}%",
            advice=advice,
            risk_level=risk_level,
            confidence=0.45,
        )
