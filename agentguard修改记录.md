# AgentGuard 修改记录

> 本记录从本项目第一次由 Codex 写入文件开始整理。  
> 时间以本机文件系统时间为主，时区按当前环境 `Asia/Shanghai` 理解。  
> 对于早期未保存逐次 patch 记录的部分，按 `progress.md`、`改动日记.md`、文件创建/修改时间和会话上下文整理，并在条目中注明。

## 记录口径

- `精确文件时间`：来自 Windows 文件系统 `CreationTime` / `LastWriteTime`。
- `上下文整理`：没有逐次 patch 时间，只能根据已有日志和会话内容合并描述。
- 用户提供的原始材料不计入 Codex 首次写文件，但作为上下文来源记录。

## 2026-06-16

### 10:06:59 - 10:12:22｜用户材料进入工作区

来源：精确文件时间。

- `作品报告（模板）.docx` 进入工作区。
- `作品原创性声明.docx` 进入工作区。
- `开放式自主命题作品赛参赛指南.pdf` 进入工作区。

说明：这些是用户/环境已有材料，不是 Codex 修改产物。后续选题和方案均基于这些材料。

### 23:28:45 - 23:28:46｜第一次由 Codex 写入项目上下文文件

来源：精确文件时间 + 上下文整理。

创建/修改文件：

- `task_plan.md`
- `findings.md`
- `progress.md`

修改内容：

- 建立 AgentGuard 项目的持续规划文件。
- 记录比赛方向：AI 衍生安全。
- 初步冻结选题为“面向 AI Agent 工具调用链的权限管控与投毒防护系统”。
- 提炼参赛材料中的提交要求、报告结构、决赛演示约束和评审重点。
- 将后续目标定义为可运行、可演示、可测试、可写报告的软件系统。

## 2026-06-17

### 10:11:02｜生成全面详细方案

来源：精确文件时间 + `progress.md` 上下文整理。

创建文件：

- `AgentGuard_全面详细方案.md`

同步修改：

- `task_plan.md`
- `findings.md`
- `progress.md`

修改内容：

- 将 AgentGuard 从初步选题扩展为完整系统方案。
- 方案覆盖：作品定位、威胁模型、总体架构、运行前扫描、运行时网关、运行后审计、数据库设计、接口设计、工程目录、测试方案、演示剧本、排期和答辩材料。
- 明确用户偏好：不是最小可行方案，而是全面详细方案。

### 10:55:33｜记录评审反馈与重构方向

来源：精确文件时间 + `改动日记.md` 上下文整理。

创建文件：

- `AgentGuard_评审反馈与重构方向.md`
- `改动日记.md`

同步修改：

- `task_plan.md`
- `findings.md`
- `progress.md`

修改内容：

- 吸收用户提供的评审反馈。
- 记录关键判断：原方案方向正确，但更像“业界最佳实践整合平台”，主创新叙事不够锋利。
- 将下一阶段重构方向确定为：面向并行子智能体的 taint-aware 权限委托与跨工具调用链验证系统。
- 新增三个重点创新方向：
  - 不可信内容污点传播。
  - capability token 与委托链验证。
  - 工具声明、源码静态行为、运行时证据三方一致性评分。

### 11:04:55｜生成重构版核心方案

来源：精确文件时间 + `progress.md` 上下文整理。

创建文件：

- `AgentGuard_重构版核心方案.md`

修改内容：

- 正式把主线从综合安全网关改为 taint-aware 并行智能体安全。
- 补充新威胁模型、taint label、taint propagation、capability token、delegation graph、工具一致性评分、MCP-aware 风险扩展。
- 设计三个强演示 case 和 baseline 对比评测。

### 14:58:05 - 15:04:04｜形成 v2 改进方案

来源：精确文件时间。

创建/修改文件：

- `AgentGuard_改进方案_v2.md`

修改内容：

- 在前一版重构方案基础上，进一步形成 v2 改进稿。
- 文件后续作为 2026-06-18 审查与收缩主线的重要参考。

## 2026-06-18

### 09:42:39｜吸收 v2 审查稿并修订主线

来源：精确文件时间 + `改动日记.md` 上下文整理。

创建文件：

- `AgentGuard_v2_审查对比记录.md`
- `AgentGuard_v2_修订大纲.md`

同步修改：

- `task_plan.md`
- `findings.md`
- `progress.md`
- `改动日记.md`

修改内容：

- 对比用户提供的 v2 审查稿和当前重构方案。
- 判断继续强调“并行智能体/capability token”会增加工程承诺和答辩风险。
- 将主线收缩为：
  - 粗粒度 taint-actionability 框架。
  - manifest、代码、运行时三方一致性审计。
  - baseline 对比与消融实验。
- 将多 Agent 传播从主创新降级为附加演示或未来扩展。
- 前端最低必做视图收缩为：taint 状态流转图、三方一致性偏差卡片、baseline 对比图。

### 09:43:50｜更新规划与上下文文件

来源：精确文件时间。

修改文件：

- `task_plan.md`
- `findings.md`
- `progress.md`
- `改动日记.md`

修改内容：

- 将 Phase 4 标记为完成。
- 将 Phase 5 以后调整为工程蓝图、后端实现、前端控制台、测试评估和参赛材料。
- 确认后续以 `AgentGuard_v2_修订大纲.md` 为更稳妥主线。

### 10:14:07｜创建 AgentGuard 工程骨架与模型层

来源：精确文件时间。

创建文件：

- `agentguard/__init__.py`
- `agentguard/backend/__init__.py`
- `agentguard/backend/app/__init__.py`
- `agentguard/backend/app/models/__init__.py`
- `agentguard/backend/app/models/schemas.py`

修改内容：

- 创建后端包结构。
- 定义基础数据模型与 schema，为 taint 状态、工具调用、审计事件、策略结果等后续模块提供类型基础。

### 10:14:44｜实现审计日志与 taint 状态机

来源：精确文件时间。

创建/修改文件：

- `agentguard/backend/app/services/audit_logger.py`
- `agentguard/backend/app/services/taint_engine.py`

修改内容：

- 实现 SQLite 审计日志记录器。
- 实现 taint 状态机和状态升级逻辑。
- 为运行时网关记录状态变化、工具调用和安全决策打基础。

后续修改：

- `audit_logger.py` 于 10:22:06 更新，配合测试修正日志行为。

### 10:15:52｜实现投毒检测与策略引擎初版

来源：精确文件时间。

创建/修改文件：

- `agentguard/backend/app/services/poisoning_detector.py`
- `agentguard/backend/app/services/policy_engine.py`
- `agentguard/backend/policies/taint_policy.yaml`

修改内容：

- 实现规则型返回值投毒检测。
- 定义策略引擎，根据 taint 状态和工具类别输出 allow / confirm / deny。
- 写入 YAML 策略规则，便于展示“安全规则可配置”。

后续修改：

- `policy_engine.py` 于 10:20:14 更新，配合网关和演示场景修正决策逻辑。

### 10:16:48｜实现供应链扫描与三方一致性分析

来源：精确文件时间。

创建/修改文件：

- `agentguard/backend/app/services/supply_chain_scanner.py`
- `agentguard/backend/app/services/consistency_analyzer.py`

修改内容：

- 实现工具源码静态扫描能力。
- 实现 manifest、静态代码、运行时证据三方一致性审计。
- 支持识别未声明网络访问、敏感路径访问、凭证读取、静默外发等偏差。

后续修改：

- `consistency_analyzer.py` 于 10:19:11 更新，配合 manifest 示例和测试用例完善风险判定。

### 10:17:36｜实现执行代理与演示工具

来源：精确文件时间。

创建/修改文件：

- `agentguard/backend/app/services/execution_proxy.py`
- `agentguard/backend/app/demo/__init__.py`
- `agentguard/backend/app/demo/tools.py`
- `agentguard/backend/app/demo/scenarios.py`

修改内容：

- 实现 execution proxy，用来采集工具运行时证据。
- 创建演示工具和场景脚本。
- 为“Agent -> Gateway -> Tool -> Postcheck”主链路提供可运行数据。

后续修改：

- `tools.py`、`scenarios.py` 于 10:20:15 更新，配合策略和测试补齐演示行为。

### 10:18:19｜实现网关与辅助服务

来源：精确文件时间。

创建文件：

- `agentguard/backend/app/services/gateway.py`
- `agentguard/backend/app/services/llm_client.py`
- `agentguard/backend/app/services/multi_agent.py`

修改内容：

- 实现统一工具调用网关。
- 将 precheck、execute、postcheck、taint 更新、审计日志串成主链路。
- 预留 LLM 调用封装，方便测试替换为 mock。
- 实现多 Agent 风险传播的轻量辅助模块，作为附加演示/未来扩展。

### 10:18:59 - 10:19:00｜创建工具 manifest 与演示数据

来源：精确文件时间。

创建/修改文件：

- `agentguard/backend/manifests/search_api.json`
- `agentguard/backend/manifests/read_public_doc.json`
- `agentguard/backend/manifests/write_report.json`
- `agentguard/backend/manifests/read_secret.json`
- `agentguard/backend/manifests/send_external.json`
- `agentguard/backend/manifests/send_internal.json`
- `agentguard/backend/manifests/weather_query.json`
- `agentguard/backend/manifests/weather_query_tampered.json`
- `agentguard/demo_data/benign/public_note.md`
- `agentguard/demo_data/benign/.env`
- `agentguard/demo_data/poisoned_returns/indirect_prompt_injection.txt`
- `agentguard/demo_data/tampered_tools/weather_tampered.py`
- `agentguard/demo_data/multi_agent/delegation_case.json`

修改内容：

- 创建正常工具、敏感读取、外发、天气查询、被篡改天气工具等 manifest。
- 创建良性文档、模拟敏感环境变量、间接提示注入文本、被篡改工具代码和多 Agent 委托样例。

后续修改：

- 部分 manifest 于 10:19:11 更新，配合一致性审计字段。
- `weather_tampered.py` 于 10:20:15 更新，补齐篡改行为证据。

### 10:19:42｜创建 FastAPI 路由和后端入口

来源：精确文件时间。

创建文件：

- `agentguard/backend/app/routers/__init__.py`
- `agentguard/backend/app/routers/gateway.py`
- `agentguard/backend/app/routers/audit.py`
- `agentguard/backend/app/routers/tools.py`
- `agentguard/backend/app/routers/demo.py`
- `agentguard/backend/app/main.py`
- `agentguard/backend/requirements.txt`

修改内容：

- 创建 FastAPI 应用入口。
- 暴露网关调用、审计记录、工具审计和演示接口。
- 写入后端依赖要求。

### 10:21:33｜创建测试与 baseline 评测

来源：精确文件时间。

创建/修改文件：

- `agentguard/backend/app/demo/baseline_eval.py`
- `agentguard/backend/tests/test_taint_gateway.py`
- `agentguard/backend/tests/test_consistency_analyzer.py`

修改内容：

- 创建 baseline 对比评测脚本。
- 添加 taint 网关测试：
  - 良性任务可写报告。
  - 外部投毒返回会隔离会话。
  - 隔离会话拒绝敏感读取。
  - 干净外部内容为 untrusted，不直接视为 trusted。
- 添加一致性分析测试：
  - 正常运行时可低风险。
  - 被篡改天气工具运行时被判严重。

后续修改：

- `test_taint_gateway.py` 于 10:22:06 更新，修正测试断言/日志配合。
- `baseline_eval.py` 于 10:31:30 更新，补齐评测模式和结果统计。

### 10:22:48 - 10:25:51｜创建前端工程并安装依赖

来源：精确文件时间。

创建/修改文件：

- `agentguard/frontend/package.json`
- `agentguard/frontend/package-lock.json`
- `agentguard/frontend/index.html`
- `agentguard/frontend/tsconfig.json`
- `agentguard/frontend/vite.config.ts`
- `agentguard/frontend/src/main.tsx`

修改内容：

- 创建 Vite + React + TypeScript 前端。
- 初步搭建四个页面入口：
  - 总览。
  - 调用链。
  - 工具审计。
  - 评测结果。
- 写入基础前端依赖。

### 10:23:42 - 10:24:53｜创建前端四个页面和初始样式

来源：精确文件时间。

创建/修改文件：

- `agentguard/frontend/src/pages/Dashboard.tsx`
- `agentguard/frontend/src/pages/CallChain.tsx`
- `agentguard/frontend/src/pages/ToolAudit.tsx`
- `agentguard/frontend/src/pages/Evaluation.tsx`
- `agentguard/frontend/src/styles/app.css`

修改内容：

- 创建总览页：运行时网关指标、taint 状态分布、最新安全决策。
- 创建调用链页：展示 taint 状态流转和审计轨迹。
- 创建工具审计页：展示三方一致性偏差卡片。
- 创建评测结果页：展示六种模式对比和假设对应关系。
- 创建全局样式文件，初步完成控制台布局、卡片、表格、状态条和动效。

### 10:30:10｜创建 README

来源：精确文件时间。

创建文件：

- `agentguard/README.md`

修改内容：

- 写入项目说明、目录结构、运行方式和核心模块介绍。

### 10:53:36｜按 `design-taste-frontend-v1` 升级前端依赖

来源：精确文件时间 + 会话上下文整理。

修改文件：

- `agentguard/frontend/package.json`
- `agentguard/frontend/package-lock.json`

修改内容：

- 加入 `@phosphor-icons/react`，将界面图标统一为 Phosphor。
- 加入 `@fontsource/geist-sans` 和 `@fontsource/jetbrains-mono`，提升前端字体现代感。
- 移除/替换早期图标依赖，避免默认感太强。

### 11:04:50 - 11:04:51｜第一轮中文化和品牌调整

来源：精确文件时间 + 会话上下文整理。

修改文件：

- `agentguard/frontend/index.html`
- `agentguard/frontend/src/pages/Evaluation.tsx`

修改内容：

- 浏览器标题改为中文：`智能体安全控制台`。
- 页面中的部分英文/技术化标题改为中文。
- 调整评测结果页文案，使其更适合中文答辩展示。

### 11:10:17 - 11:10:18｜按用户反馈统一中文、放大字号、修移动端裁切

来源：精确文件时间 + 会话上下文整理。

修改文件：

- `agentguard/frontend/src/main.tsx`
- `agentguard/frontend/src/pages/Dashboard.tsx`
- `agentguard/frontend/src/pages/CallChain.tsx`

修改内容：

- 将可访问性标签从英文改为中文：
  - `AgentGuard sections` -> `智能体安全控制台栏目`
  - `Dashboard state preview` -> `控制台状态预览`
  - `Taint propagation path` -> `污点传播路径`
- 将可见品牌名从 `AgentGuard` 转为中文表达：`智能体安全控制台`。
- 保留四个主导航：总览、调用链、工具审计、评测结果。
- 调整 Dashboard 状态切换：实时、加载中、空状态、离线。

### 11:10:56｜修复工具审计风险徽章样式映射

来源：精确文件时间 + 会话上下文整理。

修改文件：

- `agentguard/frontend/src/pages/ToolAudit.tsx`

修改内容：

- 给风险数据新增 `riskClass`。
- 修复原本中文风险值 `低/中/严重` 不能命中英文 CSS 类名的问题。
- 让低风险、中风险、严重风险徽章在亮色背景下都有正确颜色和对比度。

### 11:15:46｜最终前端视觉升级

来源：精确文件时间 + 会话上下文整理。

修改文件：

- `agentguard/frontend/src/styles/app.css`

修改内容：

- 将界面从偏暗控制台改成亮色白绿控制台。
- 整体放大字号，浏览器实测最小可见字号为 `17px`。
- 去掉容易有 AI 味的径向光斑背景，改为更克制的浅色网格和线性浅色层。
- 修复手机端顶部品牌裁切。
- 将手机导航从横向滚动改成四等分按钮，确保四个入口完整显示。
- 调整卡片、指标、表格、风险徽章、状态条、动效和间距，让界面更适合答辩展示。

### 11:15 之后｜最终验证

来源：命令输出和浏览器 QA 记录。

执行验证：

- `npm.cmd run build`
- `python -m unittest discover -s agentguard\backend\tests -v`
- Playwright 桌面与手机浏览器检查。

验证结果：

- 前端构建通过。
- 后端单测 6/6 通过。
- 桌面四页检查通过：
  - 无可见英文。
  - 无横向溢出。
  - 最小可见字号 `17px`。
- 手机四页检查通过：
  - 无可见英文。
  - 无横向溢出。
  - 顶部品牌完整显示。
  - 四个导航入口完整显示。
  - 最小可见字号 `17px`。

## 当前状态摘要

- 方案文档阶段已完成多轮收敛：全面方案 -> 并行 Agent 重构方案 -> v2 稳妥主线。
- 工程 MVP 已落盘：
  - FastAPI 后端骨架。
  - taint 引擎。
  - 投毒检测。
  - 策略引擎。
  - execution proxy。
  - 三方一致性审计。
  - SQLite 审计日志。
  - demo 数据与 baseline 评测。
  - React 前端控制台。
- 前端已按用户审美反馈调整为：
  - 全中文。
  - 更大字号。
  - 更亮颜色。
  - 更少 AI 味。
  - 手机端无裁切。

### 11:28:21 - 11:29:34｜改成固定一屏展示，取消上下滚动条

来源：精确文件时间 + 命令输出和浏览器 QA 记录。

修改文件：

- `agentguard/frontend/src/styles/app.css`

修改内容：

- 将 `html`、`body`、`#root`、`.appShell` 改为固定 `100dvh` 高度。
- 禁止页面级纵向滚动，避免浏览器出现上下滑动条。
- 将 `.mainPanel` 和 `.pageStack` 改成一屏内的固定画布布局。
- 为总览、调用链、工具审计、评测结果分别补充一屏化网格规则。
- 压缩桌面端卡片高度、间距和标题尺度，让四个页面都铺满屏幕且不溢出。
- 为手机端增加专门适配：
  - 顶部导航和品牌区压缩。
  - 总览指标改成 2×2。
  - 总览下方两块信息改成并排紧凑摘要。
  - 调用链、工具审计、评测结果都压入 390×844 视口。

验证结果：

- `npm.cmd run build` 通过。
- Playwright 桌面 1600×900 检查通过：
  - 总览、调用链、工具审计、评测结果均 `canScrollY=false`。
  - 四页均 `canScrollX=false`。
  - 主要页面块没有越出视口。
- Playwright 手机 390×844 检查通过：
  - 四页均无上下/左右滚动。
  - 顶部和底部内容没有被裁切。
  - 总览页截图确认一屏内完整展示。

### 12:00:00 - 12:30:00｜把 Demo 接入真实运行逻辑

来源：文件修改 + 后端单元测试 + Playwright 浏览器检查。

修改文件：

- `agentguard/backend/app/demo/live_demo.py`
- `agentguard/backend/app/routers/demo.py`
- `agentguard/backend/run_demo_server.py`
- `agentguard/backend/tests/test_live_demo.py`
- `agentguard/frontend/src/api/liveDemo.ts`
- `agentguard/frontend/src/context/DemoContext.tsx`
- `agentguard/frontend/src/main.tsx`
- `agentguard/frontend/src/pages/Dashboard.tsx`
- `agentguard/frontend/src/pages/CallChain.tsx`
- `agentguard/frontend/src/pages/ToolAudit.tsx`
- `agentguard/frontend/src/pages/Evaluation.tsx`
- `agentguard/frontend/src/styles/app.css`

修改内容：

- 新增 `run_live_demo()` 聚合真实演示链路：
  - 正常任务读取和写报告。
  - API 返回投毒后触发隔离。
  - 隔离状态下敏感读取和外部发送被拒绝。
  - 篡改天气工具真实执行，采集运行时读文件和外发证据。
  - 多 Agent 委托继承隔离状态。
  - 运行 baseline 六模式评测。
- 新增 `POST /demo/live/run`，供前端一键运行真实演示。
- 将每个剧本改成独立 session，避免投毒剧本污染工具审计剧本，确保篡改工具能真实跑出运行时证据。
- 将 live demo 的写报告路径改到临时目录，避免演示时覆盖或写入固定工作区文件。
- 新增无 FastAPI 依赖的 `run_demo_server.py` 标准库兜底服务：
  - 支持 `/health`。
  - 支持 `/demo/scenarios`。
  - 支持 `/demo/live/run`。
  - 返回的仍是同一套真实 `run_live_demo()` 数据，不是假数据。
- 前端新增统一数据层：
  - `runLiveDemo()` 调用后端真实接口。
  - `DemoProvider` 四页共享同一份回放数据。
  - 后端不可用时显示离线快照，避免页面空白。
- 总览页改成真实控制入口：
  - “运行真实演示”按钮。
  - 当前会话号。
  - 最终污点状态。
  - 实时指标、污点分布、最新审计决策。
- 调用链页改为后端实际步骤渲染。
- 工具审计页改为后端一致性报告渲染。
- 评测结果页改为后端 baseline_eval 真实数据渲染。
- 移动端压缩调用链节点、审计轨迹和评测表格密度，保持完整一屏展示。

验证结果：

- `python -m unittest discover -s agentguard\backend\tests -v` 通过，8/8。
- `npm.cmd run build` 通过。
- 标准库 Demo 后端 `/demo/live/run` 返回 200，返回真实 session，例如 `live-c6bf2638`。
- Playwright 桌面 1600×900 检查通过：
  - 四页均显示 `真实回放已同步`。
  - 四页均 `canScrollY=false`。
  - 四页均 `canScrollX=false`。
  - 四页均无元素越界。
- Playwright 手机 390×844 检查通过：
  - 四页均显示 `真实回放已同步`。
  - 四页均 `canScrollY=false`。
  - 四页均 `canScrollX=false`。
  - 四页均无元素越界。

### 12:30:00 - 12:36:00｜补齐真实演示复现文档和启动器

来源：README 修改 + 标准库服务启动验证 + 后端测试 + 前端构建 + 浏览器检查。

修改文件：

- `agentguard/README.md`
- `agentguard/backend/run_demo_server.py`

修改内容：

- 在 README 中补充 `POST /demo/live/run` 核心接口。
- 增加“真实演示运行”章节：
  - 标准库 Demo 后端启动命令。
  - 前端启动命令。
  - 页面自动调用真实演示接口的说明。
  - `/demo/live/run` 聚合的真实链路范围。
- 增加离线快照和 `真实回放已同步` 状态说明。
- 增加当前验证命令和最近一次验证结果。
- 将 `run_demo_server.py` 改成自包含入口，启动时自动把项目根目录加入 `sys.path`，避免直接执行脚本时报 `No module named agentguard`。

验证结果：

- 按 README 命令直接启动 `python agentguard\backend\run_demo_server.py`，`/health` 返回 200。
- `POST /demo/live/run` 返回 200，返回真实 session，例如 `live-2f133da0`。
- `python -m unittest discover -s agentguard\backend\tests -v` 通过，8/8。
- `npm.cmd run build` 通过。
- Playwright 桌面 1600×900 检查通过：
  - 四页均显示 `真实回放已同步`。
  - 四页均无上下/左右滚动。
  - 四页均无元素越界。
- Playwright 手机 390×844 检查通过：
  - 四页均显示 `真实回放已同步`。
  - 四页均无上下/左右滚动。
  - 四页均无元素越界。

### 12:36:00 - 12:45:00｜补齐文档 Part 3 答辩交付材料

来源：Prompt 套件 Part 3 要求 + README 修改 + 材料文件落盘。

修改文件：

- `agentguard/docs/答辩材料.md`
- `agentguard/README.md`

修改内容：

- 新增答辩材料文档，覆盖 Prompt 套件 Part 3 的三个输出方向：
  - 答辩叙事：问题背景、核心方法、实验验证、局限与边界。
  - 演示剧本：四个现场演示剧本，每个包含背景、操作步骤、旁白、预期反应、fallback 和评委追问。
  - 实验结果解读：核心结论、H1/H2/H2b/H3/H4 假设验证表、局限说明和答辩亮点数字。
- 明确区分“已实现”和“未来工作”，避免夸大：
  - 已实现：网关主链路、四态 taint、规则投毒检测、策略引擎、三方一致性、SQLite 审计、baseline、真实前端演示。
  - 未来工作：扩大样本量、长会话误报分析、LLM 语义增强、报告导出。
- 在 README 的演示剧本章节增加答辩材料入口。

验证结果：

- `agentguard/docs/答辩材料.md` 已存在并包含三类答辩交付内容。
- README 已引用答辩材料路径。

### 15:24:17｜按 `AUDIT_PROMPT.md` 完成功能完整性审查与修复

来源：`agentguard/AUDIT_PROMPT.md` 审查清单 + 代码修改 + 后端/前端验证。

修改文件：

- `agentguard/backend/app/services/audit_logger.py`
- `agentguard/backend/app/services/gateway.py`
- `agentguard/backend/app/services/policy_engine.py`
- `agentguard/backend/app/services/supply_chain_scanner.py`
- `agentguard/backend/app/routers/audit.py`
- `agentguard/backend/app/routers/demo.py`
- `agentguard/backend/app/routers/gateway.py`
- `agentguard/backend/app/routers/multi_agent.py`
- `agentguard/backend/app/main.py`
- `agentguard/backend/app/demo/baseline_eval.py`
- `agentguard/backend/app/demo/live_demo.py`
- `agentguard/backend/run_demo_server.py`
- `agentguard/backend/tests/test_taint_gateway.py`
- `agentguard/backend/tests/test_consistency_analyzer.py`
- `agentguard/backend/tests/test_live_demo.py`
- `agentguard/backend/tests/test_multi_agent.py`
- `agentguard/frontend/src/api/liveDemo.ts`
- `agentguard/frontend/src/context/DemoContext.tsx`
- `agentguard/frontend/src/pages/Dashboard.tsx`
- `agentguard/frontend/src/pages/CallChain.tsx`
- `agentguard/frontend/src/pages/ToolAudit.tsx`
- `agentguard/frontend/src/pages/Evaluation.tsx`
- `agentguard/pytest.ini`
- `agentguard/README.md`
- `agentguard/docs/功能完整性审查报告.md`

修改内容：

- 修复外部来源上下文进入时的 precheck 前 taint 升级逻辑，保证 `context_source` 非 `user/local/trusted` 时至少进入 `untrusted`。
- 修复策略确认逻辑：`confirmed=true` 只把原本 `confirm` 的策略升级为 `allow`，不会越权放行原本 `deny` 的调用，并记录 `manual_override`。
- 将审计日志默认 DB 从项目源码目录改到系统临时目录，并保留 `AGENTGUARD_DB` 环境变量覆盖能力。
- 新增函数粒度静态扫描：按 manifest `entrypoint` 提取指定函数 AST 子树，避免同文件其他函数污染审计结果。
- 增强静态扫描对 `ctx.read_file / ctx.write_file / ctx.http_get / ctx.http_post` 代理方法的识别。
- 新增 `POST /multi-agent/delegate` 路由，并将其注册进 FastAPI 主应用。
- 新增 `POST /gateway/sessions/{session_id}/reset`，显式暴露 reset 到 trusted 的接口。
- 增强 demo 场景接口：
  - 剧本三返回一致性审计报告。
  - 剧本四返回多 Agent 委托判定。
  - 新增 `POST /demo/evaluation/run` 评测 API。
- 增强标准库 demo server：
  - 支持自定义 `--host / --port`。
  - 支持 `/audit/events`、`/tools/manifests`、`/tools/{name}/consistency`、`/multi-agent/delegate`、`/demo/evaluation/run`。
- baseline 评测新增 `benign_sensitive` 分组，三组样例变为：良性普通任务、良性但敏感任务、攻击任务。
- 为指标计算补充代码级口径说明。
- 前端数据层新增真实端点调用：
  - Dashboard 从 `/audit/events` 聚合攻击阻断和 taint 分布。
  - CallChain 从 `/audit/events` 生成节点。
  - ToolAudit 从 `/tools/manifests` 和 `/tools/{name}/consistency` 获取数据。
  - Evaluation 从 `/demo/evaluation/run` 重跑评测。
- 新增/扩展单元测试，覆盖 taint 升级、reset、投毒检测、策略确认、一致性函数粒度扫描、多 Agent 委托和 live demo。
- 新增 `pytest.ini`，保证在 `agentguard/` 项目根目录执行 `python -m pytest backend\tests` 可直接发现顶层包。
- 新增 `agentguard/docs/功能完整性审查报告.md`，按 A-K 逐条给出状态、涉及文件和说明。
- 更新 README 中的接口、测试命令、前端真实数据来源和验证结果。

验证结果：

- `python -m compileall agentguard\backend` 通过。
- `python -m pytest backend\tests` 通过，16/16。
- `npm.cmd run build` 通过。
- FastAPI OpenAPI 检查通过，`docs_url=/docs`，路由包含：
  - `/audit/events`
  - `/demo/evaluation/run`
  - `/demo/live/run`
  - `/demo/scenarios/{scenario_id}/run`
  - `/gateway/call`
  - `/gateway/sessions/{session_id}/reset`
  - `/multi-agent/delegate`
  - `/tools/manifests`
  - `/tools/{tool_name}/consistency`
- 标准库 demo server 在 8011 端口验证通过：
  - `/health` 返回 200。
  - `/demo/live/run` 返回 `final_taint=quarantined`。
  - `/audit/events?limit=5` 返回 5 条事件。
  - `/tools/manifests` 返回 8 个 manifest。
  - `/tools/weather_query_tampered/consistency` 返回 `risk_level=critical`。
  - `/multi-agent/delegate` 对越权委托返回 `delegation_allowed=false`。
  - `/demo/evaluation/run` 返回 `case_count=6`。

遗留说明：

- 本轮曾临时创建 `agentguard/_pydeps_backend` 用于排查依赖可见性；后续已改为把 requirements 安装到当前 Python 环境并完成验证。尝试删除该临时目录时遇到异常 ACL，进一步权限修复请求被系统拒绝，因此未继续绕路清理。
