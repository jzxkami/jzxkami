import pytest

from app.schemas import AnalyzeRequest, LoginRequest, RegisterRequest


def test_stock_code_normalization():
    req = AnalyzeRequest(stock_code="600519.sh")
    assert req.stock_code == "600519.SH"


def test_news_request_fields_accept_valid_values():
    req = AnalyzeRequest(
        stock_code="600519.SH",
        include_news=True,
        news_lookback_hours=168,
        news_top_k=8,
        news_fetch_limit=300,
    )
    assert req.news_lookback_hours == 168
    assert req.news_top_k == 8
    assert req.news_fetch_limit == 300


def test_news_top_k_rejects_invalid_value():
    with pytest.raises(Exception):
        AnalyzeRequest(stock_code="600519.SH", include_news=True, news_top_k=0)


def test_register_and_login_schema_validation():
    reg = RegisterRequest(username="user_01", password="123456")
    login = LoginRequest(username="user_01", password="123456")
    assert reg.username == "user_01"
    assert login.username == "user_01"


def test_register_schema_rejects_short_password():
    with pytest.raises(Exception):
        RegisterRequest(username="user_02", password="123")
