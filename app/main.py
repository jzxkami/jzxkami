from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)
from app.services.analyzer import FinanceAnalyzer
from app.services.auth_service import AuthService, AuthUser

app = FastAPI(
    title="Finance Agent API",
    version="1.3.0",
    description="基于 Tushare + Ollama 的结构化股票分析服务（支持 K 线图 + 注册登录）",
)

settings = get_settings()
project_root = Path(__file__).resolve().parent.parent

charts_dir = project_root / settings.chart_output_dir
charts_dir.mkdir(parents=True, exist_ok=True)
web_dir = project_root / "web"
assets_dir = web_dir / "assets"

auth_db_path = project_root / settings.auth_db_path

app.mount("/charts", StaticFiles(directory=str(charts_dir)), name="charts")
app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

analyzer = FinanceAnalyzer()
auth_service = AuthService(db_path=auth_db_path, token_ttl_hours=settings.auth_token_ttl_hours)
security = HTTPBearer(auto_error=False)


def _to_user_profile(user: AuthUser) -> UserProfile:
    return UserProfile(
        user_id=user.user_id,
        username=user.username,
        created_at=user.created_at,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="未登录，请先调用 /auth/login 获取 Bearer Token。")

    user = auth_service.get_user_by_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Token 无效或已过期，请重新登录。")

    return user


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    index_file = web_dir / "index.html"
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "finance-agent", "version": "1.3.0"}


@app.post("/auth/register", response_model=UserProfile)
def register(payload: RegisterRequest) -> UserProfile:
    try:
        user = auth_service.register_user(payload.username, payload.password)
        return _to_user_profile(user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"注册失败: {exc}") from exc


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    try:
        session = auth_service.login(payload.username, payload.password)
        return TokenResponse(
            access_token=session.access_token,
            expires_at=session.expires_at,
            user=_to_user_profile(session.user),
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"登录失败: {exc}") from exc


@app.get("/auth/me", response_model=UserProfile)
def me(current_user: AuthUser = Depends(get_current_user)) -> UserProfile:
    return _to_user_profile(current_user)


@app.post("/auth/logout", response_model=LogoutResponse)
def logout(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> LogoutResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="未提供有效 Bearer Token。")

    auth_service.logout(credentials.credentials)
    return LogoutResponse(success=True)


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    payload: AnalyzeRequest,
    current_user: AuthUser = Depends(get_current_user),
) -> AnalyzeResponse:
    _ = current_user
    try:
        return analyzer.analyze(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"分析流程失败: {exc}") from exc
