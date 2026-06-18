# AgentGuard 功能完整性审查提示词

---

你是一名严格的代码审查员。请逐条对照下方的《功能要求清单》，在 AgentGuard 项目代码库中找到对应实现，判断每条要求的完成状态，并输出一份结构化审查报告。

**项目根目录**：`agentguard/`  
**判断标准**：
- ✅ 完整实现：代码存在，逻辑与要求一致，可被测试验证
- ⚠️ 部分实现：代码存在但有明显缺陷、硬编码占位符、或逻辑与要求不符
- ❌ 未实现：代码缺失或仅有注释/stub

每条给出：**状态 + 涉及文件 + 一句话说明**。审查完所有条目后，输出汇总表和未实现条目的修复建议。

---

## 功能要求清单

### A. Taint 状态机（对应文档第 5.1、7.1 节）

**A1** 存在四种 taint 状态：`trusted / untrusted / tainted / quarantined`，用枚举或常量定义，不能是裸字符串。  
**A2** 状态只能单调升级，不能降级（`trusted→untrusted→tainted→quarantined`），降级只能由显式 reset 触发。  
**A3** 外部来源内容（context_source 不是 `user/local/trusted`）进入上下文时，session 至少升级到 `untrusted`。  
**A4** 投毒检测器命中后，session 进一步升级为 `tainted` 或 `quarantined`，而不是维持 `untrusted`。  
**A5** taint 状态以 session 为粒度存储（不是单次调用临时变量），下一次工具调用时仍然有效。  
**A6** 提供显式 reset 接口（`reset_to_trusted`），重置后 session 回到 `trusted`，重置动作写入审计日志。

---

### B. 投毒检测器（对应文档第 7.2 节）

**B1** 至少覆盖以下 6 类投毒特征：`instruction_override`（规则覆盖）、`privilege_claim`（权限冒充）、`tool_inducement`（工具诱导）、`secret_request`（索取密钥）、`stealth_execution`（隐蔽执行）、`data_exfiltration`（数据外发）。  
**B2** 检测器输出包含：`poison_score`（0-100 数值）、`labels`（命中的特征列表）、`taint_status`（建议的 taint 升级目标）、`decision`（pass/flag/quarantine）。  
**B3** `poison_score > 70` 或命中 `privilege_claim / stealth_execution / secret_request` 任一 → `quarantined`；`score >= 30` 或有任意命中 → `tainted`；否则 → `untrusted`。  
**B4** 检测器是独立模块（不依赖 LLM），可在无网络环境下运行。  
**B5** 检测器在工具返回的 postcheck 阶段调用，而不是在工具执行前。

---

### C. 策略引擎（对应文档第 7.1 节决策规则表）

**C1** 存在可配置的策略规则（YAML 文件或等效配置），不能全部硬编码在 Python 函数里。  
**C2** 实现以下至少 8 条规则（session taint × tool category → decision）：
   - `trusted + *` → allow
   - `untrusted + safe_read` → allow
   - `untrusted + external_send` → deny
   - `untrusted + sensitive_read` → confirm
   - `untrusted + execute` → deny
   - `tainted + external_send` → deny
   - `tainted + sensitive_read` → deny
   - `tainted + sensitive_write` → deny
   - `quarantined + *` → deny  
**C3** 当 `confirmed=true` 时，策略引擎将原本 `confirm` 的决定升级为 `allow`，且记录 `manual_override`。  
**C4** 策略无法匹配时默认 `deny`，不允许静默放行。  
**C5** 工具调用类别（`safe_read / sensitive_read / safe_write / sensitive_write / internal_notify / external_send / execute`）来自 manifest 的 `category` 字段，而不是在 Python 中硬编码工具名。

---

### D. 工具三方一致性审计（对应文档第 5.2、7.3 节）

**D1** Manifest 声明层提取：加载 JSON manifest，至少解析 `name / description / category / permissions / allowed_paths / allowed_domains`。  
**D2** 静态层提取：通过 AST 解析源码，检测文件操作、网络请求、子进程调用、敏感字符串（.env/token/secret 等）。  
**D3** 静态扫描以**函数粒度**进行：只扫描 manifest 中 `entrypoint` 指定函数的 AST 子树，而不是扫描整个源文件。（如果当前是文件级扫描，标记为 ⚠️ 部分实现。）  
**D4** 运行时层提取：通过 Execution Proxy 采集实际访问路径、实际访问域名、实际发出请求和权限类型，不依赖工具自报。  
**D5** 三类偏差检测均有实现：`manifest_static_mismatch`（声明 vs 静态）、`manifest_runtime_mismatch`（声明 vs 运行时）、`undeclared_path/undeclared_network`（路径/域名越界）。  
**D6** 输出 `consistency_score`（0-100）和 `risk_level`（low/medium/high/critical），分级逻辑与文档一致：有任意 critical 偏差 → risk=critical。  
**D7** 暴露 HTTP 端点 `GET /tools/{name}/consistency`，可通过 API 触发一致性审计。

---

### E. Execution Proxy（对应文档第 7.3 节运行时证据采集机制）

**E1** 所有 demo 工具通过统一的 ExecutionProxy 执行，不允许直接调用工具函数绕过代理。  
**E2** 代理记录以下证据：实际读写路径（`paths`）、实际访问域名（`domains`）、实际发出的请求摘要（`requests`）、触发的权限类型（`permissions`）。  
**E3** 运行时证据在工具执行完成后写入审计日志（`event_type = "runtime_evidence"`）。

---

### F. 多 Agent 场景（对应文档第 5.3、7.4 节）

**F1** 存在委托审判逻辑：给定父 Agent taint 状态 + 子 Agent 申请权限，判断是否允许委托。  
**F2** taint 状态不可降级继承：子 Agent 继承的 taint 不低于父 Agent 的 taint。  
**F3** 子 Agent 申请的权限不得超出父 Agent 拥有的权限范围，否则委托被拒绝。  
**F4** `quarantined` 状态的内容不得委托给子 Agent。  
**F5** 多 Agent 委托逻辑暴露 HTTP 端点（`POST /multi-agent/delegate` 或等效）。

---

### G. 审计日志（对应文档第 7.1、9.1 节）

**G1** 审计日志使用持久化存储（SQLite 或等效），不能只存内存。  
**G2** 记录以下四类事件：`precheck`（调用前决策）、`postcheck`（返回值投毒检测结果）、`runtime_evidence`（运行时行为证据）、`taint_transition`（taint 状态变更）。  
**G3** 每条日志包含：`session_id / event_type / tool_name / taint_before / taint_after / decision / timestamp`。  
**G4** 暴露 HTTP 端点 `GET /audit/events`，支持按 `session_id` 过滤和 `limit` 分页。  
**G5** 审计日志的 DB 文件路径支持通过环境变量 `AGENTGUARD_DB` 覆盖，默认写入系统临时目录（而非项目源码目录）。

---

### H. 四个演示剧本（对应文档第 10 节）

**H1** 剧本一「正常任务通过」：至少包含一个安全读取步骤和一个普通写入步骤，两步均应得到 `decision=allow`，session 保持 `trusted`。  
**H2** 剧本二「API 返回投毒触发 taint」：搜索 API 返回含投毒内容，后续敏感读取和外部发送均被 `deny`，session 升级为 `tainted` 或 `quarantined`。  
**H3** 剧本三「skill 篡改一致性检测」：运行篡改后的工具，运行时越界行为（读取 `.env`、访问非白名单域名）被一致性审计发现，`risk_level` 为 `high` 或 `critical`。  
**H4** 剧本四「多 Agent 风险传播」：外部内容经由一个 Agent 传递，使后续 Agent 的敏感读取被拒绝，体现 taint 跨 Agent 传播。  
**H5** 四个剧本均通过 `POST /demo/scenarios/{id}/run` 可一键触发，响应包含每步的 `decision` 和 `taint_status`。

---

### I. 评测体系（对应文档第 8 节）

**I1** 定义了 6 种对比模式（无防护 / 仅 approval / 仅规则 / 全量-taint / 全量-一致性 / AgentGuard 全量）中至少前 3 种的测试路径，且可通过 API 或脚本触发。  
**I2** 测试样例按三组拆分：良性普通任务 / 良性但敏感任务 / 攻击任务，三组均有实际可运行的 demo case。  
**I3** 指标口径有代码级定义（不能只是文档里的文字描述）：攻击拦截率、误报率、任务完成率至少有注释或函数说明其分子分母定义。  
**I4** 前端评测页面（Evaluation）展示的数据来自真实 API 调用（而非全部硬编码）。

---

### J. 前端界面（对应文档第 11 节工程落地）

**J1** Dashboard 页面展示的指标数据（攻击拦截数、taint 状态分布）来自 `GET /audit/events` 的实时聚合，而非硬编码。  
**J2** CallChain（调用链）页面展示的节点来自 `GET /audit/events` 的真实审计事件，而非静态数组。  
**J3** ToolAudit（工具审计）页面的工具列表来自 `GET /tools/manifests`，一致性分数来自 `GET /tools/{name}/consistency`。  
**J4** 前端 `npm run build` 无报错可成功构建。

---

### K. 服务启动与工程质量

**K1** 存在启动脚本（`run.sh` 或 `Makefile` 或 `README` 里的完整启动命令），可一条命令启动后端。  
**K2** 后端启动后，`GET /docs`（Swagger UI）正常加载，所有路由可见。  
**K3** 单元测试覆盖至少：taint 状态机升级逻辑、投毒检测器命中逻辑、策略引擎决策逻辑、一致性审计偏差检测。  
**K4** 所有测试通过 `python -m pytest backend/tests/` 可运行，无需特殊环境变量。

---

## 输出格式要求

请按以下格式输出审查报告：

```
## 审查报告

### 逐条结果

| # | 要求 | 状态 | 涉及文件 | 说明 |
|---|------|------|----------|------|
| A1 | 四态 taint 枚举 | ✅ | models/schemas.py | TaintStatus 枚举已定义 |
| A2 | 状态单调升级 | ✅ | services/taint_engine.py | max_status() 保证只升不降 |
| D3 | 函数粒度静态扫描 | ⚠️ | services/supply_chain_scanner.py | 当前扫描整个文件，缺少按函数名提取 AST 子树 |
...（所有条目）

### 汇总

- ✅ 完整实现：X 条
- ⚠️ 部分实现：X 条  
- ❌ 未实现：X 条

### 修复建议（仅针对 ⚠️ 和 ❌）

**D3 函数粒度静态扫描**  
问题：...  
建议：...
```

---

审查时请实际读取代码文件，不要凭印象判断。对于 ⚠️ 条目，请引用具体的代码行或函数名说明缺陷所在。
