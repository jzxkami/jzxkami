from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import FinanceAnalyzer

app = FastAPI(
    title="Finance Agent API",
    version="1.2.0",
    description="基于 Tushare + Ollama 的结构化股票分析服务（支持 K 线图）",
)

settings = get_settings()
project_root = Path(__file__).resolve().parent.parent

charts_dir = project_root / settings.chart_output_dir
charts_dir.mkdir(parents=True, exist_ok=True)
web_dir = project_root / "web"
assets_dir = web_dir / "assets"

app.mount("/charts", StaticFiles(directory=str(charts_dir)), name="charts")
app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

analyzer = FinanceAnalyzer()


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    index_file = web_dir / "index.html"
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "finance-agent", "version": "1.2.0"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyzer.analyze(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"分析流程失败: {exc}") from exc
