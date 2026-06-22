const sceneConfig = {
  campus: {
    name: "校园生活服务小程序",
    modules: ["闲置交易", "求购信息", "校园拼车", "失物招领", "消息中心", "校园认证"],
    roles: "普通学生、发布者、认证用户、管理员",
  },
  idle: {
    name: "校园闲置交易",
    modules: ["商品发布", "商品列表", "分类筛选", "搜索", "收藏联系", "交易状态"],
    roles: "买家、卖家、管理员",
  },
  ride: {
    name: "校园拼车互助",
    modules: ["发起拼车", "路线搜索", "时间筛选", "同行联系", "订单状态", "安全提醒"],
    roles: "发起人、同行者、管理员",
  },
  lost: {
    name: "失物招领",
    modules: ["发布寻物", "发布招领", "物品分类", "地点筛选", "联系认领", "信息下架"],
    roles: "失主、拾取者、管理员",
  },
};

const moduleTemplates = {
  闲置交易: ["商品标题", "价格", "图片", "分类", "联系方式", "交易状态"],
  求购信息: ["求购物品", "预算", "需求描述", "有效时间", "联系方式"],
  校园拼车: ["起点", "终点", "出发时间", "人数", "备注", "状态"],
  失物招领: ["物品名称", "丢失/拾取地点", "时间", "图片", "联系方式", "处理状态"],
  消息中心: ["消息类型", "标题", "内容", "已读状态", "创建时间"],
  校园认证: ["姓名", "学号", "学院", "认证状态", "审核说明"],
  商品发布: ["标题", "价格", "图片", "分类", "描述", "库存状态"],
  商品列表: ["商品名称", "价格", "封面图", "浏览量", "发布时间"],
  分类筛选: ["分类名称", "排序规则", "筛选条件", "结果数量"],
  搜索: ["关键词", "分类", "匹配结果", "搜索历史"],
  收藏联系: ["收藏状态", "联系入口", "用户信息", "消息记录"],
  交易状态: ["在售", "已预定", "已售出", "下架"],
  发起拼车: ["起点", "终点", "时间", "人数", "费用说明"],
  路线搜索: ["起点关键词", "终点关键词", "匹配路线", "距离"],
  时间筛选: ["日期", "时间段", "剩余座位", "状态"],
  同行联系: ["发起人", "联系方式", "备注", "安全提示"],
  订单状态: ["待成行", "已满员", "已取消", "已完成"],
  安全提醒: ["实名认证", "路线确认", "紧急联系人", "举报入口"],
  发布寻物: ["物品名", "丢失地点", "丢失时间", "图片", "联系方式"],
  发布招领: ["物品名", "拾取地点", "拾取时间", "图片", "认领方式"],
  物品分类: ["证件", "电子产品", "钥匙", "书籍", "服饰"],
  地点筛选: ["教学楼", "宿舍", "食堂", "操场", "图书馆"],
  联系认领: ["联系方式", "认领说明", "核验问题", "状态"],
  信息下架: ["下架原因", "处理人", "处理时间", "备注"],
};

const requirementEl = document.getElementById("requirement");
const sceneEl = document.getElementById("scene");
const generateBtn = document.getElementById("generateBtn");
const exportBtn = document.getElementById("exportBtn");
const panels = {
  modules: document.getElementById("modules"),
  sop: document.getElementById("sop"),
  tests: document.getElementById("tests"),
  prompt: document.getElementById("prompt"),
  resume: document.getElementById("resume"),
};

let latestMarkdown = "";

function buildModules(config) {
  return config.modules.map((moduleName, index) => ({
    id: index + 1,
    moduleName,
    page: `${moduleName}页`,
    fields: moduleTemplates[moduleName] || ["标题", "描述", "状态", "创建时间"],
    dependency: index === 0 ? "登录/基础数据" : `${config.modules[Math.max(0, index - 1)]}数据`,
    testPoint: "字段完整性、空状态、权限限制、异常提示",
  }));
}

function renderModules(modules, config) {
  const rows = modules
    .map(
      (item) => `
      <tr>
        <td>${item.moduleName}</td>
        <td>${item.page}</td>
        <td>${item.fields.join("、")}</td>
        <td>${item.dependency}</td>
        <td>${item.testPoint}</td>
      </tr>
    `,
    )
    .join("");

  panels.modules.innerHTML = `
    <div class="section-title">
      <h2>功能模块拆解</h2>
      <span class="tag">${config.name}</span>
    </div>
    <div class="note">核心思路：先识别用户角色和使用场景，再拆分页面、字段、依赖和验收点。</div>
    <table>
      <thead>
        <tr>
          <th>模块</th>
          <th>页面</th>
          <th>关键字段</th>
          <th>依赖</th>
          <th>测试点</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderSop(config) {
  const steps = [
    "需求澄清：确认用户角色、使用场景、核心目标和边界条件。",
    "模块拆解：将需求拆为页面、功能、字段、状态和权限。",
    "流程设计：梳理从入口到结果页的用户路径，并补充异常流程。",
    "接口与数据整理：列出每个模块需要的字段、数据来源和依赖关系。",
    "测试验收：针对正常流程、空数据、权限不足、提交失败等情况设计测试点。",
    "文档沉淀：输出需求说明、SOP、流程图、测试清单和项目复盘。",
  ];

  panels.sop.innerHTML = `
    <div class="section-title">
      <h2>开发 SOP</h2>
      <span class="tag">可复制执行</span>
    </div>
    <ol>${steps.map((step) => `<li>${step}</li>`).join("")}</ol>
  `;
}

function renderTests(modules) {
  const tests = modules.flatMap((item) => [
    `${item.moduleName}：校验必填字段为空时是否给出明确提示。`,
    `${item.moduleName}：验证无数据状态、加载状态和失败状态是否完整。`,
    `${item.moduleName}：检查未登录或未认证用户是否被正确拦截。`,
  ]);

  panels.tests.innerHTML = `
    <div class="section-title">
      <h2>测试清单</h2>
      <span class="tag">${tests.length} 项</span>
    </div>
    <ul>${tests.map((test) => `<li>${test}</li>`).join("")}</ul>
  `;
}

function renderPrompt(config, requirement) {
  const prompt = `你是一名服务产品实习生，擅长需求分析、SOP 编写和 AI Agent 流程拆解。

请基于以下小程序需求，输出结构化分析结果：

【项目场景】
${config.name}

【原始需求】
${requirement}

【输出要求】
1. 拆解用户角色、使用场景和核心目标
2. 输出功能模块表：模块、页面、字段、依赖、测试点
3. 编写开发 SOP：需求澄清 -> 模块拆解 -> 流程设计 -> 测试验收 -> 文档沉淀
4. 输出测试清单，覆盖正常流程、异常流程、权限限制、空状态
5. 将人工流程拆成 AI Agent 可执行步骤
6. 最后生成一段适合写进简历的项目经历`;

  panels.prompt.innerHTML = `
    <div class="section-title">
      <h2>Prompt 模板</h2>
      <span class="tag">面试可讲</span>
    </div>
    <pre class="prompt-box">${prompt}</pre>
  `;

  return prompt;
}

function renderResume(config) {
  const resume = `小程序需求拆解与 SOP 生成器｜个人项目

项目简介：基于校园生活服务类小程序项目复盘，设计并实现需求拆解工具，将模糊业务需求转化为功能模块、页面字段、开发 SOP、测试清单和 Prompt 模板。

项目职责：
1. 围绕 ${config.name} 场景，梳理用户角色、业务流程、页面结构和核心功能模块。
2. 将复杂需求拆解为模块、字段、依赖、状态和测试点，形成结构化需求清单。
3. 设计开发 SOP 和测试清单，覆盖需求澄清、模块拆解、流程设计、联调验证和文档沉淀。
4. 编写 Prompt 模板，将人工需求分析过程转化为 AI Agent 可执行的标准化步骤。

项目亮点：体现了结构化拆解、SOP 编写、Prompt 设计和项目文档沉淀能力，与服务产品实习生岗位高度匹配。`;

  panels.resume.innerHTML = `
    <div class="section-title">
      <h2>简历描述</h2>
      <span class="tag">可直接改写</span>
    </div>
    <pre class="resume-box">${resume}</pre>
  `;

  return resume;
}

function buildMarkdown(config, requirement, modules, prompt, resume) {
  const moduleRows = modules
    .map((item) => `| ${item.moduleName} | ${item.page} | ${item.fields.join("、")} | ${item.dependency} | ${item.testPoint} |`)
    .join("\n");

  return `# ${config.name}需求拆解报告

## 原始需求
${requirement}

## 功能模块
| 模块 | 页面 | 关键字段 | 依赖 | 测试点 |
| --- | --- | --- | --- | --- |
${moduleRows}

## 开发 SOP
1. 需求澄清：确认用户角色、使用场景、核心目标和边界条件。
2. 模块拆解：将需求拆为页面、功能、字段、状态和权限。
3. 流程设计：梳理从入口到结果页的用户路径，并补充异常流程。
4. 接口与数据整理：列出每个模块需要的字段、数据来源和依赖关系。
5. 测试验收：针对正常流程、空数据、权限不足、提交失败等情况设计测试点。
6. 文档沉淀：输出需求说明、SOP、流程图、测试清单和项目复盘。

## Prompt 模板
\`\`\`text
${prompt}
\`\`\`

## 简历描述
${resume}
`;
}

function generate() {
  const config = sceneConfig[sceneEl.value];
  const requirement = requirementEl.value.trim();
  const modules = buildModules(config);

  renderModules(modules, config);
  renderSop(config);
  renderTests(modules);
  const prompt = renderPrompt(config, requirement);
  const resume = renderResume(config);
  latestMarkdown = buildMarkdown(config, requirement, modules, prompt, resume);
}

function exportMarkdown() {
  if (!latestMarkdown) generate();
  const blob = new Blob([latestMarkdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "campus-sop-report.md";
  link.click();
  URL.revokeObjectURL(url);
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(button.dataset.target).classList.add("active");
  });
});

generateBtn.addEventListener("click", generate);
exportBtn.addEventListener("click", exportMarkdown);
sceneEl.addEventListener("change", generate);
generate();
