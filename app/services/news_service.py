from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

import tushare as ts

from app.config import get_settings
from app.schemas import NewsEvidence
from app.services.ttl_cache import TTLCache


@dataclass
class _ScoredNews:
    item: NewsEvidence
    score: float
    pub_dt: dt.datetime


@dataclass
class NewsFetchResult:
    items: list[NewsEvidence]
    prompt_items: list[str]
    cache_hit: bool
    stale_fallback_used: bool
    warnings: list[str]
    effective_lookback_hours: int
    effective_top_k: int
    effective_fetch_limit: int
    major_count: int
    news_count: int


class NewsRAGService:
    def __init__(self) -> None:
        settings = get_settings()
        self._pro = None
        self.lookback_hours = settings.news_lookback_hours
        self.top_k = settings.news_top_k
        self.fetch_limit = settings.news_fetch_limit

        self._cache: TTLCache[tuple[str, str, int, int, int], list[NewsEvidence]] = TTLCache(
            ttl_seconds=settings.news_cache_ttl_seconds,
            maxsize=settings.news_cache_maxsize,
        )
        self._stale_cache: TTLCache[tuple[str, str], list[NewsEvidence]] = TTLCache(
            ttl_seconds=settings.news_stale_cache_ttl_seconds,
            maxsize=settings.news_stale_cache_maxsize,
        )

    def _ensure_client(self):
        settings = get_settings()
        if not settings.tushare_token:
            raise RuntimeError("未读取到 TUSHARE_TOKEN，请在 .env 或环境变量中配置后重试")
        if self._pro is None:
            self._pro = ts.pro_api(settings.tushare_token)
        return self._pro

    def get_cache_stats(self) -> dict[str, dict[str, int]]:
        return {
            "fresh": self._cache.stats(),
            "stale": self._stale_cache.stats(),
        }

    def fetch_related_news(
        self,
        stock_code: str,
        stock_name: str,
        lookback_hours: int | None = None,
        top_k: int | None = None,
        fetch_limit: int | None = None,
    ) -> NewsFetchResult:
        effective_lookback_hours = self._pick_int(lookback_hours, self.lookback_hours)
        effective_top_k = self._pick_int(top_k, self.top_k)
        effective_fetch_limit = self._pick_int(fetch_limit, self.fetch_limit)
        effective_top_k = min(effective_top_k, effective_fetch_limit)

        cache_key = (
            stock_code,
            stock_name or stock_code,
            effective_lookback_hours,
            effective_top_k,
            effective_fetch_limit,
        )
        stale_key = (stock_code, stock_name or stock_code)

        hit, cached = self._cache.get(cache_key)
        if hit and cached is not None:
            copied = self._copy_items(cached)
            return NewsFetchResult(
                items=copied,
                prompt_items=self._to_prompt_items(copied),
                cache_hit=True,
                stale_fallback_used=False,
                warnings=[],
                effective_lookback_hours=effective_lookback_hours,
                effective_top_k=effective_top_k,
                effective_fetch_limit=effective_fetch_limit,
                major_count=0,
                news_count=0,
            )

        now = dt.datetime.now()
        start = now - dt.timedelta(hours=effective_lookback_hours)
        start_str = start.strftime("%Y-%m-%d %H:%M:%S")
        end_str = now.strftime("%Y-%m-%d %H:%M:%S")

        major_records, major_warn = self._fetch_major_news(start_str, end_str, effective_fetch_limit)
        news_records, news_warn = self._fetch_news(start_str, end_str, effective_fetch_limit)

        warnings = self._merge_warnings([major_warn, news_warn])

        merged = major_records + news_records
        ranked = self._rank_news(merged, stock_code, stock_name, now)

        related = [x for x in ranked if x.score >= 2.0]
        if not related:
            # 没有强相关时，回退到最近宏观新闻，避免 include_news=true 却无上下文。
            related = ranked[: min(effective_top_k, len(ranked))]

        selected = [x.item for x in related[:effective_top_k]]

        if selected:
            self._cache.set(cache_key, selected)
            self._stale_cache.set(stale_key, selected)
            copied = self._copy_items(selected)
            return NewsFetchResult(
                items=copied,
                prompt_items=self._to_prompt_items(copied),
                cache_hit=False,
                stale_fallback_used=False,
                warnings=warnings,
                effective_lookback_hours=effective_lookback_hours,
                effective_top_k=effective_top_k,
                effective_fetch_limit=effective_fetch_limit,
                major_count=len(major_records),
                news_count=len(news_records),
            )

        stale_hit, stale_cached = self._stale_cache.get(stale_key)
        if stale_hit and stale_cached:
            copied = self._copy_items(stale_cached)
            warnings.append("当前时间窗无可用新新闻，已回退到最近缓存新闻。")
            return NewsFetchResult(
                items=copied,
                prompt_items=self._to_prompt_items(copied),
                cache_hit=False,
                stale_fallback_used=True,
                warnings=self._merge_warnings(warnings),
                effective_lookback_hours=effective_lookback_hours,
                effective_top_k=effective_top_k,
                effective_fetch_limit=effective_fetch_limit,
                major_count=len(major_records),
                news_count=len(news_records),
            )

        if not warnings:
            warnings = ["新闻 RAG 已启用，但当前时间窗未检索到可用新闻。"]

        return NewsFetchResult(
            items=[],
            prompt_items=[],
            cache_hit=False,
            stale_fallback_used=False,
            warnings=warnings,
            effective_lookback_hours=effective_lookback_hours,
            effective_top_k=effective_top_k,
            effective_fetch_limit=effective_fetch_limit,
            major_count=len(major_records),
            news_count=len(news_records),
        )

    def _fetch_major_news(
        self,
        start_str: str,
        end_str: str,
        limit: int,
    ) -> tuple[list[NewsEvidence], str | None]:
        records: list[NewsEvidence] = []
        try:
            pro = self._ensure_client()
            df = pro.major_news(start_date=start_str, end_date=end_str, limit=limit)
            if df is None or df.empty:
                return records, None

            for row in df.to_dict(orient="records"):
                title = str(row.get("title") or "").strip()
                if not title:
                    continue

                pub_time = str(row.get("pub_time") or "")
                source = str(row.get("src") or "财联社").strip() or "财联社"
                url = str(row.get("url") or "").strip() or None

                records.append(
                    NewsEvidence(
                        title=title,
                        pub_time=pub_time,
                        source=source,
                        url=url,
                        snippet=title,
                    )
                )
        except Exception as exc:
            return records, self._format_fetch_error("major_news", exc)

        return records, None

    def _fetch_news(
        self,
        start_str: str,
        end_str: str,
        limit: int,
    ) -> tuple[list[NewsEvidence], str | None]:
        records: list[NewsEvidence] = []
        try:
            pro = self._ensure_client()
            df = pro.news(start_date=start_str, end_date=end_str, limit=limit)
            if df is None or df.empty:
                return records, None

            for row in df.to_dict(orient="records"):
                content = str(row.get("content") or "").strip()
                title = str(row.get("title") or "").strip()
                if not title:
                    title = self._extract_title_from_content(content)
                if not title:
                    continue

                pub_time = str(row.get("datetime") or "")
                snippet = self._trim_text(content, 120)

                records.append(
                    NewsEvidence(
                        title=title,
                        pub_time=pub_time,
                        source="TushareNews",
                        url=None,
                        snippet=snippet,
                    )
                )
        except Exception as exc:
            return records, self._format_fetch_error("news", exc)

        return records, None

    @staticmethod
    def _extract_title_from_content(content: str) -> str:
        if not content:
            return ""
        match = re.match(r"^【([^】]{2,80})】", content)
        if match:
            return match.group(1).strip()
        return NewsRAGService._trim_text(content, 30)

    @staticmethod
    def _trim_text(text: str, max_len: int) -> str:
        s = (text or "").replace("\n", " ").strip()
        if len(s) <= max_len:
            return s
        return s[: max_len - 1] + "…"

    @staticmethod
    def _parse_pub_time(value: str, fallback: dt.datetime) -> dt.datetime:
        if not value:
            return fallback
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return dt.datetime.strptime(value, fmt)
            except ValueError:
                continue
        return fallback

    @staticmethod
    def _score_news(item: NewsEvidence, keywords: list[str], now: dt.datetime) -> tuple[float, dt.datetime]:
        pub_dt = NewsRAGService._parse_pub_time(item.pub_time, now)

        title_u = (item.title or "").upper()
        snippet_u = (item.snippet or "").upper()
        score = 0.0

        for kw in keywords:
            if not kw:
                continue
            k = kw.upper()
            if k in title_u:
                score += 4.0
            if k in snippet_u:
                score += 2.0

        hours = max(0.0, (now - pub_dt).total_seconds() / 3600.0)
        recency_bonus = max(0.0, 1.5 - (hours / 48.0) * 1.5)
        score += recency_bonus
        return score, pub_dt

    def _rank_news(
        self,
        items: list[NewsEvidence],
        stock_code: str,
        stock_name: str,
        now: dt.datetime,
    ) -> list[_ScoredNews]:
        if not items:
            return []

        code_plain = stock_code.split(".")[0].strip()
        keywords = [stock_name.strip(), code_plain]
        keywords = [k for k in keywords if k]

        scored: list[_ScoredNews] = []
        seen: set[tuple[str, str]] = set()

        for item in items:
            key = (item.title, item.pub_time)
            if key in seen:
                continue
            seen.add(key)

            score, pub_dt = self._score_news(item, keywords, now)
            item.relevance = round(score, 3)
            scored.append(_ScoredNews(item=item, score=score, pub_dt=pub_dt))

        scored.sort(key=lambda x: (x.score, x.pub_dt), reverse=True)
        return scored

    @staticmethod
    def _to_prompt_items(items: list[NewsEvidence]) -> list[str]:
        result: list[str] = []
        for x in items:
            src = x.source or "资讯"
            when = x.pub_time or "未知时间"
            snippet = x.snippet or x.title
            result.append(f"[{when}] {src}：{x.title}；摘要：{snippet}")
        return result

    @staticmethod
    def _copy_items(items: list[NewsEvidence]) -> list[NewsEvidence]:
        return [item.model_copy(deep=True) for item in items]

    @staticmethod
    def _pick_int(candidate: int | None, default: int) -> int:
        if candidate is None:
            return int(default)
        return int(candidate)

    @staticmethod
    def _is_rate_limit_error(message: str) -> bool:
        if not message:
            return False
        keywords = ("每小时最多访问", "每分钟最多访问", "频次", "限流", "积分", "权限")
        return any(k in message for k in keywords)

    def _format_fetch_error(self, endpoint: str, exc: Exception) -> str:
        raw = self._trim_text(str(exc), 120)
        if self._is_rate_limit_error(raw):
            return f"{endpoint} 接口限流或权限不足：{raw}"
        return f"{endpoint} 接口调用失败：{raw}"

    @staticmethod
    def _merge_warnings(items: list[str | None]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for x in items:
            msg = (x or "").strip()
            if not msg:
                continue
            if msg in seen:
                continue
            seen.add(msg)
            result.append(msg)
        return result
