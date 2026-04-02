from datetime import datetime

from app.schemas import NewsEvidence
from app.services.news_service import NewsRAGService


def test_extract_title_from_content_brackets():
    s = "【茅台发布一季度业绩】公司营收同比增长"
    title = NewsRAGService._extract_title_from_content(s)
    assert title == "茅台发布一季度业绩"


def test_score_news_keyword_in_title():
    item = NewsEvidence(
        title="贵州茅台发布2026一季报",
        pub_time="2026-04-01 12:00:00",
        source="测试",
        snippet="营收利润双增",
    )
    score, _ = NewsRAGService._score_news(item, ["贵州茅台", "600519"], datetime(2026, 4, 1, 12, 30, 0))
    assert score >= 4.0


def test_fetch_related_news_uses_stale_cache_when_rate_limited(monkeypatch):
    service = NewsRAGService()

    stale_item = NewsEvidence(
        title="贵州茅台渠道反馈平稳",
        pub_time="2026-04-01 10:00:00",
        source="测试",
        snippet="库存维持健康",
    )
    service._stale_cache.set(("600519.SH", "贵州茅台"), [stale_item])

    monkeypatch.setattr(
        service,
        "_fetch_major_news",
        lambda *_: ([], "major_news 接口限流或权限不足：每小时最多访问该接口2次"),
    )
    monkeypatch.setattr(
        service,
        "_fetch_news",
        lambda *_: ([], "news 接口限流或权限不足：每小时最多访问该接口5次"),
    )

    result = service.fetch_related_news("600519.SH", "贵州茅台")

    assert result.stale_fallback_used is True
    assert len(result.items) == 1
    assert result.items[0].title == "贵州茅台渠道反馈平稳"
    assert any("已回退到最近缓存新闻" in x for x in result.warnings)


def test_fetch_related_news_empty_has_generic_warning(monkeypatch):
    service = NewsRAGService()

    monkeypatch.setattr(service, "_fetch_major_news", lambda *_: ([], None))
    monkeypatch.setattr(service, "_fetch_news", lambda *_: ([], None))

    result = service.fetch_related_news("600519.SH", "贵州茅台")

    assert result.stale_fallback_used is False
    assert result.items == []
    assert "新闻 RAG 已启用，但当前时间窗未检索到可用新闻。" in result.warnings


def test_fetch_related_news_accepts_runtime_overrides(monkeypatch):
    service = NewsRAGService()

    major_item = NewsEvidence(
        title="贵州茅台新品发布会",
        pub_time="2026-04-01 09:00:00",
        source="测试",
        snippet="新品策略升级",
    )
    news_item = NewsEvidence(
        title="贵州茅台渠道调研反馈",
        pub_time="2026-04-01 11:00:00",
        source="测试",
        snippet="终端动销平稳",
    )

    monkeypatch.setattr(service, "_fetch_major_news", lambda *_: ([major_item], None))
    monkeypatch.setattr(service, "_fetch_news", lambda *_: ([news_item], None))

    result = service.fetch_related_news(
        "600519.SH",
        "贵州茅台",
        lookback_hours=168,
        top_k=1,
        fetch_limit=300,
    )

    assert result.effective_lookback_hours == 168
    assert result.effective_top_k == 1
    assert result.effective_fetch_limit == 300
    assert result.major_count == 1
    assert result.news_count == 1
    assert len(result.items) == 1
