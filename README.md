# Finance Agent

一个可部署的 AI 金融分析后端：用 `Tushare` 拉取行情，用 `Ollama` 做推理，用 `FastAPI` 对外提供结构化 JSON 接口。

## 项目亮点（面试版）
- 脚本工程化：从单机脚本升级为 RESTful API，支持网页/小程序/其他服务调用。
- 结构化输出：LLM 结果强制 JSON 并用 Pydantic 校验，前端可直接渲染卡片。
- 风险兜底：模型异常时自动退化到规则引擎，保证接口永远可解析。
- 可扩展架构：预留 `include_news` 字段，为下一步 RAG 新闻增强做兼容。

## 目录结构

```text
.
├── app
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 环境配置
│   ├── schemas.py              # 请求/响应数据模型
│   └── services
│       ├── analyzer.py         # 业务编排
│       ├── data_service.py     # Tushare 数据拉取与指标计算
│       └── ai_service.py       # Ollama 推理与 JSON 解析兜底
├── Finance_Agent.py            # CLI 入口（复用同一服务层）
├── tests
│   └── test_schema.py
├── requirements.txt
└── .env.example
```

## 快速开始

1. 创建并激活虚拟环境。
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置环境变量：
   ```bash
   cp .env.example .env
   ```
   并填写 `TUSHARE_TOKEN`。
4. 启动 Ollama（确保 `llama3` 模型可用）。
5. 启动 API：
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## API 示例

### 健康检查
```bash
curl http://127.0.0.1:8000/health
```

### 分析接口
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519.SH",
    "stock_name": "贵州茅台",
    "lookback_days": 20,
    "include_news": false
  }'
```

返回示例（节选）：
```json
{
  "stock_code": "600519.SH",
  "price_summary": {
    "trend": "up",
    "period_change_pct": 3.21
  },
  "ai_insight": {
    "trend": "up",
    "risk_level": "medium",
    "confidence": 0.72
  }
}
```

## GitHub 展示建议
- 发布一个 60 秒 Demo：`/analyze` 请求 + Swagger 页面 + JSON 结果。
- 在仓库 README 放系统架构图和接口截图。
- 下一阶段加分项：Redis 缓存、新闻 RAG、单元测试覆盖率、Dockerfile。
