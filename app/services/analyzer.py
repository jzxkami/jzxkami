from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.config import get_settings
from app.schemas import AnalyzeRequest, AnalyzeResponse, CacheInfo, NewsDebug
from app.services.ai_service import AIService
from app.services.chart_service import ChartService
from app.services.data_service import MarketDataService
from app.services.news_service import NewsRAGService


class FinanceAnalyzer:
    def __init__(self) -> None:
        self.data_service = MarketDataService()
        self.ai_service = AIService()
        self.chart_service = ChartService()
        self.news_service = NewsRAGService()

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        settings = get_settings()
        warnings: list[str] = []
        news_items_for_prompt: list[str] = []
        news_evidences = []
        news_hit: bool | None = None
        news_stale_fallback_used: bool | None = None
        news_debug = NewsDebug(requested=request.include_news)

        chart_url: str | None = None
        chart_file: str | None = None

        df, daily_hit = self.data_service.fetch_recent_daily_with_cache(
            stock_code=request.stock_code,
            lookback_days=request.lookback_days or settings.default_lookback_days,
        )
        price_summary = self.data_service.build_price_summary(df)
        rows = self.data_service.build_prompt_rows(df, settings.max_rows_for_prompt)

        if request.stock_name:
            stock_name = request.stock_name
            stock_name_hit = False
        else:
            stock_name, stock_name_hit = self.data_service.resolve_stock_name_with_cache(request.stock_code)

        if request.include_news:
            news_result = self.news_service.fetch_related_news(
                stock_code=request.stock_code,
                stock_name=stock_name,
                lookback_hours=request.news_lookback_hours,
                top_k=request.news_top_k,
                fetch_limit=request.news_fetch_limit,
            )
            news_evidences = news_result.items
            news_items_for_prompt = news_result.prompt_items
            news_hit = news_result.cache_hit
            news_stale_fallback_used = news_result.stale_fallback_used
            warnings.extend(news_result.warnings)

            news_debug = NewsDebug(
                requested=True,
                effective_lookback_hours=news_result.effective_lookback_hours,
                effective_top_k=news_result.effective_top_k,
                effective_fetch_limit=news_result.effective_fetch_limit,
                major_count=news_result.major_count,
                news_count=news_result.news_count,
                selected_count=len(news_evidences),
                cache_hit=news_result.cache_hit,
                stale_fallback_used=news_result.stale_fallback_used,
            )

        if request.include_chart:
            try:
                chart_file, _ = self.chart_service.render_candlestick(df, request.stock_code, stock_name)
                chart_url = f"/charts/{chart_file}"
            except Exception as exc:
                warnings.append(f"K 线图生成失败: {exc}")

        ai_insight = self.ai_service.analyze(
            stock_code=request.stock_code,
            stock_name=stock_name,
            price_summary=price_summary,
            rows=rows,
            news_items=news_items_for_prompt,
        )

        cache_stats = self.data_service.get_cache_stats()
        news_cache_stats = self.news_service.get_cache_stats()
        news_fresh_stats = news_cache_stats["fresh"]

        cache_info = CacheInfo(
            daily_hit=daily_hit,
            stock_name_hit=stock_name_hit,
            news_hit=news_hit,
            news_stale_fallback_used=news_stale_fallback_used,
            daily_hits_total=int(cache_stats["daily"]["hits"]),
            daily_misses_total=int(cache_stats["daily"]["misses"]),
            stock_name_hits_total=int(cache_stats["stock_name"]["hits"]),
            stock_name_misses_total=int(cache_stats["stock_name"]["misses"]),
            news_hits_total=int(news_fresh_stats["hits"]),
            news_misses_total=int(news_fresh_stats["misses"]),
        )

        return AnalyzeResponse(
            request_id=str(uuid4()),
            stock_code=request.stock_code,
            stock_name=stock_name,
            generated_at=datetime.now(),
            price_summary=price_summary,
            ai_insight=ai_insight,
            chart_url=chart_url,
            chart_file=chart_file,
            cache_info=cache_info,
            used_news_items=len(news_evidences),
            news_items=news_evidences,
            news_debug=news_debug,
            warnings=warnings,
        )
