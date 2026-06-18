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

安装依赖：

```powershell
cd agentguard\backend
python -m pip install -r requirements.txt
```

启动 API：

```powershell
cd ..\..
uvicorn agentguard.backend.app.main:app --reload
```

核心 API：

- `POST /gateway/call`
- `GET /audit/events`
- `GET /tools/manifests`
- `GET /tools/{tool_name}/consistency`
- `POST /demo/scenarios/{scenario_id}/run`
- `POST /demo/live/run`
- `POST /demo/evaluation/run`
- `POST /multi-agent/delegate`
- `POST /gateway/sessions/{session_id}/reset`

审计日志默认写入系统临时目录 `Temp\agentguard\agentguard_audit.db`，也可以通过环境变量 `AGENTGUARD_DB` 指定路径。

## 真实演示运行

如果已经安装 FastAPI 依赖，可以直接用上面的 API 服务。为了答辩现场更稳，项目也提供一个只依赖 Python 标准库的演示服务，接口路径保持一致：

```powershell
cd agentguard\..
python agentguard\backend\run_demo_server.py
```

然后启动前端：

```powershell
cd agentguard\frontend
npm.cmd run dev
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
cd agentguard
python -m pytest backend\tests
```

也可以用标准库 `unittest` 运行：

```powershell
python -m unittest discover -s backend\tests -v
```

baseline 评测入口：

```powershell
python -m agentguard.backend.app.demo.baseline_eval
```

当前 MVP 样例输出口径：

| 模式 | 良性任务完成率 | 攻击拦截率 | 误报率 |
|---|---:|---:|---:|
| no_guard | 100% | 0% | 0% |
| approval_only | 100% | 67% | 0% |
| rule_only | 100% | 33% | 0% |
| agentguard_minus_taint | 100% | 33% | 0% |
| agentguard_minus_consistency | 100% | 100% | 0% |
| agentguard | 100% | 100% | 0% |

## 前端运行

```powershell
cd agentguard\frontend
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
- Evaluation：从 `POST /demo/evaluation/run` 渲染六模式 baseline 对比

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
- H3：通过 `weather_query_tampered` 的运行时越界域名和路径证明三方一致性审计
- H4：通过正常天气工具与篡改天气工具的风险等级差异区分潜在危险和实际危险

## 工程边界

这个 MVP 明确只评估通过 execution proxy 接入的受控工具生态。它不做 token 级精细污点追踪，不做任意第三方二进制 syscall 监控，也不实现完整 MCP/OAuth 协议。

## 当前验证命令

```powershell
cd agentguard
python -m pytest backend\tests
cd frontend
npm.cmd run build
```

最近一次验证结果：

- 后端 pytest 16/16 通过。
- 前端生产构建通过。
- 桌面 `1600×900` 与手机 `390×844` 浏览器检查通过：四页均无上下/左右滚动，且状态显示“真实回放已同步”。
