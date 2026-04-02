# Finance Agent

一个可部署的 AI 金融分析后端：用 `Tushare` 拉取行情，用 `Ollama` 推理，用 `FastAPI` 提供结构化 JSON 接口，并自动生成 K 线图。

## 项目亮点
- 可视化前端页面：输入股票代码后直接展示分析结果与 K 线图，不用 Swagger。
- 注册登录鉴权：支持用户注册、登录、`Bearer Token` 鉴权，`/analyze` 需登录后访问。
- 动态查询任意股票：按 `stock_code` 实时拉取行情，不是预设股票。
- 新闻 RAG 生效：`include_news=true` 时检索新闻并回传证据列表。
- 新闻降级兜底：新闻接口限流/权限不足时返回明确 warning，并尝试回退到最近缓存新闻。
- 内存缓存优化（TTL）：同日同参数重复查询直接命中缓存，减少 Tushare 调用次数。

## 目录结构

```text
.
├── app
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   └── services
│       ├── analyzer.py
│       ├── ai_service.py
│       ├── auth_service.py
│       ├── data_service.py
│       ├── news_service.py
│       ├── chart_service.py
│       └── ttl_cache.py
├── deploy
│   ├── README.md
│   ├── systemd/
│   ├── nginx/
│   └── scripts/
├── web
│   ├── index.html
│   └── assets
├── tests
└── .env.example
```

## 本地启动

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
```bash
cp .env.example .env
```
至少填写：
- `TUSHARE_TOKEN`
- `OLLAMA_HOST`（默认 `http://localhost:11434`）

3. 启动服务
```bash
uvicorn app.main:app --reload --port 8000
```

4. 打开页面
```text
http://127.0.0.1:8000/
```

## API 使用流程（先登录，再分析）

1. 注册
```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user","password":"demo123456"}'
```

2. 登录（拿到 `access_token`）
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user","password":"demo123456"}'
```

3. 调分析接口（必须带 Bearer）
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <你的access_token>" \
  -d '{
    "stock_code": "600519.SH",
    "include_news": true,
    "include_chart": true,
    "news_lookback_hours": 168,
    "news_top_k": 8,
    "news_fetch_limit": 300
  }'
```

## 云端部署（Ubuntu 22.04）

完整步骤见：
- [deploy/README.md](/Users/jzxkami/Desktop/AI_Project/deploy/README.md)

部署方式：
- `systemd` 托管 `uvicorn`
- `nginx` 反向代理
- 可选 `certbot` 开 HTTPS
