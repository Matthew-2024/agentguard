# AgentGuard Prototype

AgentGuard 是一个部署在 AI Agent 与工具调用链之间的安全控制层。这个原型按 `AgentGuard Prompt 套件 v1` 落地，重点实现三件事：

- Agent -> Gateway -> Tool -> Postcheck 主链路
- 四态 taint 控制：`trusted / untrusted / tainted / quarantined`
- 工具 manifest / 静态扫描 / 运行时证据三方一致性审计

## 目录

```text
agentguard/
  backend/
    app/
      main.py
      models/
      routers/
      services/
        gateway.py
        taint_engine.py
        poisoning_detector.py
        policy_engine.py
        consistency_analyzer.py
        supply_chain_scanner.py
        audit_logger.py
        execution_proxy.py
        llm_client.py
      demo/
        scenarios.py
        tools.py
        baseline_eval.py
        live_demo.py
    policies/
    manifests/
    tests/
  frontend/
    src/
      pages/
        Dashboard.tsx
        CallChain.tsx
        ToolAudit.tsx
        Evaluation.tsx
  demo_data/
```

## 后端运行

以下命令默认从仓库根目录 `E:\study\code\agent_guard\agentguard` 执行。Python 命令使用工作区根目录虚拟环境 `..\venv\Scripts\python.exe`。

安装依赖：

```powershell
..\venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

启动 API：

```powershell
.\scripts\start-backend.ps1
```

标准库演示服务：

```powershell
.\scripts\start-backend.ps1 -DemoServer
```

如果需要手工运行 FastAPI，从工作区根目录执行：

```powershell
cd ..
.\venv\Scripts\python.exe -m uvicorn agentguard.backend.app.main:app --reload
```

核心 API：

- `POST /gateway/call`
- `GET /health`
- `GET /audit/events`
- `GET /tools/manifests`
- `GET /tools/{tool_name}/consistency`
- `POST /demo/scenarios/{scenario_id}/run`
- `POST /demo/live/run`
- `POST /demo/evaluation/run`
- `POST /multi-agent/delegate`
- `POST /gateway/sessions/{session_id}/reset`
- `GET /report/latest`
- `GET /report/latest.md`
- `GET /report/session/{session_id}`
- `GET /report/session/{session_id}.md`

审计日志默认写入系统临时目录 `Temp\agentguard\agentguard_audit.db`，也可以通过环境变量 `AGENTGUARD_DB` 指定路径。

## 真实演示运行

如果已经安装 FastAPI 依赖，可以直接用上面的 API 服务。为了答辩现场更稳，项目也提供一个只依赖 Python 标准库的演示服务，接口路径保持一致：

```powershell
.\scripts\start-backend.ps1 -DemoServer
```

然后启动前端：

```powershell
cd frontend
npm.cmd run dev
cd ..
```

也可以一键启动后端和前端：

```powershell
.\scripts\start-demo.ps1
```

如果希望启动后等待后端 `/health` 和前端首页可访问：

```powershell
.\scripts\start-demo.ps1 -Wait
```

单独检查本地演示健康状态：

```powershell
.\scripts\check-demo.ps1
```

停止一键启动的本地演示进程：

```powershell
.\scripts\stop-demo.ps1
```

打开 `http://127.0.0.1:5173/`，总览页会自动调用 `POST http://127.0.0.1:8000/demo/live/run`。点击“运行真实演示”会重新执行一次真实链路，而不是刷新静态数据。

`/demo/live/run` 会聚合以下真实结果：

- 正常公开资料读取和普通报告写入。
- 外部 API 返回投毒后触发 `quarantined`。
- 隔离状态下敏感读取和外部发送被拒绝。
- 篡改天气工具真实执行，采集读文件和外发域名证据。
- 多 Agent 委托继承隔离状态。
- 六种 baseline / 消融评测结果。

## 本地测试

当前环境安装依赖后可直接用 `pytest` 跑核心测试：

```powershell
..\venv\Scripts\python.exe -m pytest backend\tests
```

也可以用标准库 `unittest` 运行：

```powershell
..\venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

baseline 评测入口：

```powershell
cd ..
.\venv\Scripts\python.exe -m agentguard.backend.app.demo.baseline_eval
cd agentguard
```

扩展 benchmark 和压力测试入口：

```powershell
cd ..
.\venv\Scripts\python.exe -m agentguard.backend.app.demo.benchmark
cd agentguard
```

当前代码 benchmark 复现门禁：

```powershell
.\scripts\verify-benchmark.ps1
```

API 入口：

- `POST /demo/evaluation/run`：MVP 六模式 baseline。
- `POST /demo/benchmark/run`：扩展 benchmark、一致性良性/异常对照、串行压力测试和并发压力测试。

标准库演示服务也支持：

```powershell
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/demo/benchmark/run?repetitions=10&pressure_iterations=200"
```

一键验证：

```powershell
.\scripts\verify.ps1
```

如果只验证后端：

```powershell
.\scripts\verify.ps1 -SkipFrontend
```

密钥扫描门禁：

```powershell
.\scripts\scan-secrets.ps1
```

提交文件集合门禁：

```powershell
.\scripts\verify-release-files.ps1
```

正式 benchmark 结果门禁：

```powershell
.\scripts\verify-results.ps1
```

该脚本只读取 `results/main_benchmark_with_consistency_precheck_*/benchmark.json`，检查样本数、baseline/消融模式、taint 贡献、一致性良性对照、precheck 阻断率和压力测试字段，不会重新生成或改写实验结果。

Docker 完整部署：

```powershell
docker compose up --build
```

Docker 配置和镜像构建验证：

```powershell
.\scripts\verify-docker.ps1
```

完整最终审计会执行本地验证、密钥扫描、diff 检查、权威 benchmark 阈值检查和 Docker runtime 验证：

```powershell
.\scripts\final-audit.ps1
```

如果本机 Docker Desktop 未启动，只跑本地非容器审计：

```powershell
.\scripts\final-audit.ps1 -SkipDocker
```

保存正式 Benchmark 结果：

```powershell
.\scripts\save-benchmark.ps1 -ExperimentName "main_benchmark"
```

容器模式会启动：

- `agentguard-api`：`http://127.0.0.1:8000`
- `agentguard-web`：`http://127.0.0.1:5173`

前端容器通过 `/api` 反向代理访问后端；本地 Vite 开发仍可使用 `.\scripts\start-frontend.ps1` 指向 `http://127.0.0.1:8000`。

CI 配置见 `.github/workflows/ci.yml`，会运行本地最终审计、Docker compose config 和 Docker build。

正式实验结果不要手工改写到 README。运行 `POST /demo/benchmark/run` 或 `python -m agentguard.backend.app.demo.benchmark` 后，将原始 JSON 放入 `results/<实验名称>_<时间戳>/`。

## 前端运行

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

生产构建：

```powershell
npm.cmd run build
```

控制台包含四个页面：

- Dashboard：从 `GET /audit/events` 聚合运行态指标和 taint 状态分布
- CallChain：从 `GET /audit/events` 渲染调用链审计节点
- ToolAudit：从 `GET /tools/manifests` 和 `GET /tools/{tool_name}/consistency` 渲染偏差卡片
- Evaluation：从 `POST /demo/evaluation/run` 渲染六模式 baseline 对比，并可调用 `POST /demo/benchmark/run` 展示扩展 benchmark、良性/异常工具对照、串行压力测试和并发吞吐摘要
- Evaluation 页面提供 `GET /report/latest.md` 报告导出入口

如果后端未启动，前端会显示离线快照，避免空白；后端启动成功后侧边栏状态会显示“真实回放已同步”。

## 演示剧本

`agentguard/backend/app/demo/scenarios.py` 内置四个剧本：

- `benign_task_passes`：公开资料读取和普通报告写入通过
- `poisoned_api_triggers_taint`：外部 API 返回投毒，session 升级并阻断敏感读取/外发
- `tampered_tool_consistency`：天气工具被篡改后读取 `.env` 并访问未知域名
- `multi_agent_taint_propagation`：子 Agent 继承 taint，不能触发高危工具

答辩可用材料见 `agentguard/docs/答辩材料.md`，包含：

- 问题背景 / 核心方法 / 实验验证 / 局限与边界。
- 四个现场演示剧本的操作步骤、旁白、预期反应和 fallback。
- 实验结果解读、假设验证表、局限说明和答辩亮点数字。

## 假设映射

- H1：通过良性任务完成率比较 approval-only 与 AgentGuard
- H2：通过投毒后敏感读取/外发拦截比较 rule-only、去 taint 消融与 AgentGuard
- H3：通过多类篡改工具的运行时越界域名和路径证明三方一致性审计
- H4：通过正常天气工具与篡改天气工具的风险等级差异区分潜在危险和实际危险

## 工程边界

这个 MVP 明确只评估通过 execution proxy 接入的受控工具生态。它不做 token 级精细污点追踪，不做任意第三方二进制 syscall 监控，也不实现完整 MCP/OAuth 协议。

实验指标、消融口径和运行时证据边界见 `docs/实验说明.md`。工程交付和结果归档要求见 `docs/工程交付说明.md`。
交给队友继续开发或复验时，先看 `docs/队友交付说明.md` 和 `docs/提交与验收清单.md`。

## 当前验证命令

```powershell
.\scripts\verify.ps1
.\scripts\verify.ps1 -SkipFrontend
.\scripts\verify-docker.ps1
cd frontend
npm.cmd install
npm.cmd run build
```

最近一次正式结果以 `results/` 下的原始文件为准。README 不维护易过期的通过数量和百分比。
