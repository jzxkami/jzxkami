from app.schemas import AnalyzeRequest


def test_stock_code_normalization():
    req = AnalyzeRequest(stock_code="600519.sh")
    assert req.stock_code == "600519.SH"
