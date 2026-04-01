from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import FinanceAnalyzer

app = FastAPI(
    title="Finance Agent API",
    version="1.0.0",
    description="基于 Tushare + Ollama 的结构化股票分析服务",
)

analyzer = FinanceAnalyzer()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "finance-agent", "version": "1.0.0"}


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
