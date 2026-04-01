# Finance Agent

一个可部署的 AI 金融分析后端：用 `Tushare` 拉取行情，用 `Ollama` 推理，用 `FastAPI` 提供结构化 JSON 接口，并自动生成 K 线图。

## 项目亮点
- 可视化前端页面：输入股票代码后直接展示分析结果与 K 线图，不用 Swagger。
- 动态查询任意股票：按 `stock_code` 实时拉取行情，不是预设股票。
- 结构化输出：LLM 结果强制 JSON，前端可直接渲染。
- 内存缓存优化（TTL）：同日同参数重复查询直接命中缓存，减少 Tushare 调用次数。
- 服务化落地：从本地脚本升级为 REST API，可被多端调用。

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
│       ├── data_service.py
│       ├── chart_service.py
│       └── ttl_cache.py
├── web
│   ├── index.html
│   └── assets
│       ├── styles.css
│       └── app.js
├── Finance_Agent.py
├── tests
│   ├── test_schema.py
│   └── test_ttl_cache.py
├── requirements.txt
└── .env.example
```

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
```bash
cp .env.example .env
```
填写 `TUSHARE_TOKEN`。

3. 启动服务
```bash
uvicorn app.main:app --reload --port 8000
```

## 可视化页面

启动后直接打开：
```text
http://127.0.0.1:8000/
```

页面会调用 `/analyze`，并在返回 `chart_url` 时直接渲染 K 线图。

## API 示例

### 健康检查
```bash
curl http://127.0.0.1:8000/health
```

### 分析接口（动态股票 + K 线图 + 缓存信息）
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519.SH",
    "lookback_days": 20,
    "include_news": false,
    "include_chart": true
  }'
```

返回示例（节选）：
```json
{
  "stock_code": "600519.SH",
  "stock_name": "贵州茅台",
  "chart_url": "/charts/600519.SH_20260401_234507.png",
  "cache_info": {
    "daily_hit": true,
    "stock_name_hit": true,
    "daily_hits_total": 1,
    "daily_misses_total": 1,
    "stock_name_hits_total": 1,
    "stock_name_misses_total": 1
  }
}
```
