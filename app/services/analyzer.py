from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.config import get_settings
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.ai_service import AIService
from app.services.data_service import MarketDataService


class FinanceAnalyzer:
    def __init__(self) -> None:
        self.data_service = MarketDataService()
        self.ai_service = AIService()

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        settings = get_settings()
        warnings: list[str] = []
        news_items: list[str] = []

        if request.include_news:
            warnings.append("include_news=true 已接收；新闻 RAG 功能将在下一阶段接入。")

        df = self.data_service.fetch_recent_daily(
            stock_code=request.stock_code,
            lookback_days=request.lookback_days or settings.default_lookback_days,
        )
        price_summary = self.data_service.build_price_summary(df)
        rows = self.data_service.build_prompt_rows(df, settings.max_rows_for_prompt)

        stock_name = request.stock_name or request.stock_code
        ai_insight = self.ai_service.analyze(
            stock_code=request.stock_code,
            stock_name=stock_name,
            price_summary=price_summary,
            rows=rows,
            news_items=news_items,
        )

        return AnalyzeResponse(
            request_id=str(uuid4()),
            stock_code=request.stock_code,
            stock_name=stock_name,
            generated_at=datetime.now(),
            price_summary=price_summary,
            ai_insight=ai_insight,
            used_news_items=len(news_items),
            warnings=warnings,
        )
