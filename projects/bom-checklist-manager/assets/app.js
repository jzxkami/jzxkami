const STORAGE_KEY = "bom-checklist-manager-items";

const demoItems = [
  {
    moduleName: "闲置交易",
    featureName: "发布商品",
    pageName: "发布页",
    fields: "标题、价格、图片、分类、联系方式",
    dependency: "登录、校园认证、图片上传",
    testPoint: "必填校验、图片上传、发布成功、失败提示",
    status: "已完成",
  },
  {
    moduleName: "闲置交易",
    featureName: "商品列表",
    pageName: "闲置大厅",
    fields: "商品名、价格、封面图、分类、浏览量",
    dependency: "商品数据接口、分类数据",
    testPoint: "分类筛选、搜索、空状态、加载状态",
    status: "开发中",
  },
  {
    moduleName: "校园拼车",
    featureName: "发起拼车",
    pageName: "拼车大厅",
    fields: "起点、终点、出发时间、人数、备注",
    dependency: "登录、校园认证",
    testPoint: "时间校验、人数限制、取消发布",
    status: "待确认",
  },
  {
    moduleName: "失物招领",
    featureName: "发布招领",
    pageName: "寻物招领",
    fields: "物品名、拾取地点、图片、联系方式、认领说明",
    dependency: "登录、图片上传",
    testPoint: "联系方式校验、图片为空、信息下架",
    status: "开发中",
  },
  {
    moduleName: "消息中心",
    featureName: "消息通知",
    pageName: "消息中心",
    fields: "消息类型、标题、内容、已读状态、创建时间",
    dependency: "用户系统、通知数据",
    testPoint: "已读未读、空消息、消息分类",
    status: "待确认",
  },
];

let items = loadItems();

const form = document.getElementById("bomForm");
const body = document.getElementById("bomBody");
const exportBtn = document.getElementById("exportBtn");
const loadDemoBtn = document.getElementById("loadDemoBtn");
const clearBtn = document.getElementById("clearBtn");
const sopList = document.getElementById("sopList");
const totalCount = document.getElementById("totalCount");
const doneCount = document.getElementById("doneCount");
const todoCount = document.getElementById("todoCount");
const rateText = document.getElementById("rateText");

function loadItems() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) return demoItems;
  try {
    return JSON.parse(saved);
  } catch {
    return demoItems;
  }
}

function saveItems() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

function statusClass(status) {
  if (status === "已完成") return "status-done";
  if (status === "开发中") return "status-progress";
  return "status-todo";
}

function renderTable() {
  body.innerHTML = items
    .map(
      (item, index) => `
      <tr>
        <td>${item.moduleName}</td>
        <td>${item.featureName}</td>
        <td>${item.pageName}</td>
        <td>${item.fields}</td>
        <td>${item.dependency || "-"}</td>
        <td>${item.testPoint || "-"}</td>
        <td><span class="status ${statusClass(item.status)}">${item.status}</span></td>
        <td><button class="delete" data-index="${index}">删除</button></td>
      </tr>
    `,
    )
    .join("");

  document.querySelectorAll(".delete").forEach((button) => {
    button.addEventListener("click", () => {
      items.splice(Number(button.dataset.index), 1);
      saveItems();
      render();
    });
  });
}

function renderMetrics() {
  const total = items.length;
  const done = items.filter((item) => item.status === "已完成").length;
  const todo = items.filter((item) => item.status === "待确认").length;
  const rate = total ? Math.round((done / total) * 100) : 0;

  totalCount.textContent = total;
  doneCount.textContent = done;
  todoCount.textContent = todo;
  rateText.textContent = `${rate}%`;
}

function renderSop() {
  const steps = [
    "建立 BOM 清单：按模块整理子功能、页面、字段、依赖关系和测试点。",
    "核对字段完整性：检查每个功能是否具备输入字段、输出结果和状态流转。",
    "识别依赖关系：标记登录、认证、上传、消息、接口等前置条件。",
    "补充验收标准：为每个功能添加正常流程、异常流程、空状态和权限校验。",
    "更新交付状态：按待确认、开发中、已完成追踪项目推进情况。",
    "沉淀文档：导出 Markdown，用于项目复盘、简历材料和面试讲解。",
  ];

  sopList.innerHTML = steps.map((step) => `<li>${step}</li>`).join("");
}

function render() {
  renderTable();
  renderMetrics();
  renderSop();
}

function getFormData() {
  return {
    moduleName: document.getElementById("moduleName").value.trim(),
    featureName: document.getElementById("featureName").value.trim(),
    pageName: document.getElementById("pageName").value.trim(),
    fields: document.getElementById("fields").value.trim(),
    dependency: document.getElementById("dependency").value.trim(),
    testPoint: document.getElementById("testPoint").value.trim(),
    status: document.getElementById("status").value,
  };
}

function buildMarkdown() {
  const rows = items
    .map(
      (item) =>
        `| ${item.moduleName} | ${item.featureName} | ${item.pageName} | ${item.fields} | ${item.dependency || "-"} | ${item.testPoint || "-"} | ${item.status} |`,
    )
    .join("\n");

  return `# 功能 BOM 与测试清单

## 项目简介

本项目用于将小程序功能拆解为标准化 BOM 清单，统一管理模块、子功能、页面、字段、依赖关系、测试点和交付状态。

## 功能 BOM

| 模块 | 子功能 | 页面 | 字段 | 依赖 | 测试点 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
${rows}

## 项目 SOP

1. 建立 BOM 清单：按模块整理子功能、页面、字段、依赖关系和测试点。
2. 核对字段完整性：检查每个功能是否具备输入字段、输出结果和状态流转。
3. 识别依赖关系：标记登录、认证、上传、消息、接口等前置条件。
4. 补充验收标准：为每个功能添加正常流程、异常流程、空状态和权限校验。
5. 更新交付状态：按待确认、开发中、已完成追踪项目推进情况。
6. 沉淀文档：导出 Markdown，用于项目复盘、简历材料和面试讲解。

## 简历描述

设计并实现“功能 BOM 与测试清单管理器”，基于校园小程序项目将闲置交易、拼车、失物招领和消息中心等功能拆解为模块、页面、字段、依赖关系和测试点；通过状态统计和 Markdown 导出，实现需求清单整理、功能核对、测试验收和项目文档沉淀，体现了结构化拆解、BOM 整理和 SOP 标准化能力。
`;
}

function exportMarkdown() {
  const blob = new Blob([buildMarkdown()], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "bom-checklist-report.md";
  link.click();
  URL.revokeObjectURL(url);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = getFormData();
  if (!data.moduleName || !data.featureName || !data.pageName || !data.fields) return;
  items.unshift(data);
  saveItems();
  render();
});

loadDemoBtn.addEventListener("click", () => {
  items = demoItems;
  saveItems();
  render();
});

clearBtn.addEventListener("click", () => {
  if (!confirm("确定清空所有清单吗？")) return;
  items = [];
  saveItems();
  render();
});

exportBtn.addEventListener("click", exportMarkdown);
render();
