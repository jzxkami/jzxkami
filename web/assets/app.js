const form = document.getElementById("analyze-form");
const stockCodeInput = document.getElementById("stock-code");
const stockNameInput = document.getElementById("stock-name");
const lookbackInput = document.getElementById("lookback-days");
const includeChartInput = document.getElementById("include-chart");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");

const resultTitle = document.getElementById("result-title");
const resultTime = document.getElementById("result-time");
const trendText = document.getElementById("trend-text");
const volatilityText = document.getElementById("volatility-text");
const adviceText = document.getElementById("advice-text");
const riskText = document.getElementById("risk-text");
const metricGrid = document.getElementById("metric-grid");
const chartWrap = document.getElementById("chart-wrap");
const chartImage = document.getElementById("chart-image");
const chartLink = document.getElementById("chart-link");
const cacheText = document.getElementById("cache-text");
const warningsBox = document.getElementById("warnings-box");
const rawJson = document.getElementById("raw-json");

const trendMap = {
  up: "上涨",
  down: "下跌",
  sideways: "震荡",
};

const riskMap = {
  low: "低",
  medium: "中",
  high: "高",
};

function setStatus(text, type = "idle") {
  statusEl.textContent = text;
  statusEl.className = `status ${type}`;
}

function fmtNum(value) {
  if (typeof value !== "number") return "-";
  return Number(value).toLocaleString("zh-CN", { maximumFractionDigits: 4 });
}

function renderMetrics(summary) {
  const items = [
    ["区间", `${summary.start_date} ~ ${summary.end_date}`],
    ["最新收盘", fmtNum(summary.latest_close)],
    ["区间涨跌(%)", fmtNum(summary.period_change_pct)],
    ["最高价", fmtNum(summary.high)],
    ["最低价", fmtNum(summary.low)],
    ["振幅价差", fmtNum(summary.high_low_spread)],
    ["振幅(%)", fmtNum(summary.high_low_spread_pct)],
    ["平均成交量", fmtNum(summary.avg_volume)],
    ["趋势标签", trendMap[summary.trend] || summary.trend],
  ];

  metricGrid.innerHTML = items
    .map(
      ([label, value]) =>
        `<div class="metric-item"><strong>${label}</strong><span>${value}</span></div>`,
    )
    .join("");
}

function renderCache(cacheInfo) {
  if (!cacheInfo) {
    cacheText.textContent = "本次未返回缓存信息。";
    return;
  }

  cacheText.textContent = `行情缓存: ${cacheInfo.daily_hit ? "命中" : "未命中"}（累计命中 ${cacheInfo.daily_hits_total} / 未命中 ${cacheInfo.daily_misses_total}）；` +
    `名称缓存: ${cacheInfo.stock_name_hit ? "命中" : "未命中"}（累计命中 ${cacheInfo.stock_name_hits_total} / 未命中 ${cacheInfo.stock_name_misses_total}）`;
}

function renderWarnings(warnings = []) {
  if (!warnings.length) {
    warningsBox.hidden = true;
    warningsBox.innerHTML = "";
    return;
  }
  warningsBox.hidden = false;
  warningsBox.innerHTML = warnings.map((w) => `<div>• ${w}</div>`).join("");
}

function renderResult(data) {
  const ai = data.ai_insight;
  const summary = data.price_summary;

  resultTitle.textContent = `${data.stock_name} (${data.stock_code})`;
  resultTime.textContent = `生成时间：${new Date(data.generated_at).toLocaleString("zh-CN")}`;

  trendText.textContent = `${trendMap[ai.trend] || ai.trend}。${ai.reason}`;
  volatilityText.textContent = ai.volatility;
  adviceText.textContent = ai.advice;
  riskText.textContent = `风险等级：${riskMap[ai.risk_level] || ai.risk_level}，置信度：${fmtNum(ai.confidence)}`;

  renderMetrics(summary);
  renderCache(data.cache_info);
  renderWarnings(data.warnings);

  if (data.chart_url) {
    chartWrap.hidden = false;
    const src = `${data.chart_url}?v=${Date.now()}`;
    chartImage.src = src;
    chartLink.href = data.chart_url;
  } else {
    chartWrap.hidden = true;
    chartImage.removeAttribute("src");
    chartLink.href = "#";
  }

  rawJson.textContent = JSON.stringify(data, null, 2);
}

function normalizePayload() {
  const stockCode = stockCodeInput.value.trim().toUpperCase();
  const stockName = stockNameInput.value.trim();
  const lookbackDays = Number(lookbackInput.value);

  return {
    stock_code: stockCode,
    stock_name: stockName || null,
    lookback_days: Number.isFinite(lookbackDays) ? lookbackDays : 20,
    include_news: false,
    include_chart: includeChartInput.checked,
  };
}

async function analyzeStock(evt) {
  evt.preventDefault();
  const payload = normalizePayload();

  setStatus("正在分析中，请稍候...", "loading");
  submitBtn.disabled = true;

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      const err = Array.isArray(data.detail)
        ? data.detail.map((x) => x.msg).join("; ")
        : data.detail || "请求失败";
      throw new Error(err);
    }

    renderResult(data);
    setStatus("分析完成。", "success");
  } catch (err) {
    setStatus(`分析失败：${err.message}`, "error");
  } finally {
    submitBtn.disabled = false;
  }
}

form.addEventListener("submit", analyzeStock);

for (const btn of document.querySelectorAll(".quick")) {
  btn.addEventListener("click", () => {
    stockCodeInput.value = btn.dataset.code;
    stockNameInput.value = "";
    setStatus(`已选择 ${btn.dataset.code}，点击“开始分析”执行。`, "idle");
  });
}
