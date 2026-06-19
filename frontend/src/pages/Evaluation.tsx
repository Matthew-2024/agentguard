import React from "react";
import { ChartBar, DownloadSimple, Gauge, Play, ShieldWarning } from "@phosphor-icons/react";
import { useDemo } from "../context/DemoContext";
import { BenchmarkResult, downloadLatestReport, runBenchmark, runEvaluation } from "../api/liveDemo";

export function Evaluation() {
  const { data } = useDemo();
  const [loading, setLoading] = React.useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = React.useState(false);
  const [reportLoading, setReportLoading] = React.useState(false);
  const [rows, setRows] = React.useState(data.baseline.rows);
  const [benchmark, setBenchmark] = React.useState<BenchmarkResult | null>(null);

  React.useEffect(() => {
    setRows(data.baseline.rows);
  }, [data.baseline.rows]);

  const rerun = React.useCallback(async () => {
    setLoading(true);
    try {
      const baseline = await runEvaluation();
      setRows(baseline.rows);
    } finally {
      setLoading(false);
    }
  }, []);

  const rerunBenchmark = React.useCallback(async () => {
    setBenchmarkLoading(true);
    try {
      const result = await runBenchmark();
      setBenchmark(result);
      setRows(result.basic_benchmark.rows);
    } finally {
      setBenchmarkLoading(false);
    }
  }, []);

  const exportReport = React.useCallback(async () => {
    setReportLoading(true);
    try {
      await downloadLatestReport();
    } finally {
      setReportLoading(false);
    }
  }, []);

  return (
    <section className="pageStack">
      <header className="pageHeader">
        <div>
          <p className="eyebrow">基线对比</p>
          <h1>评测结果</h1>
        </div>
        <button type="button" className="actionChip" onClick={() => void rerun()} disabled={loading}>
          <Play size={17} weight="fill" />
          <span>{loading ? "重算中" : "重跑评测"}</span>
        </button>
        <button type="button" className="actionChip" onClick={() => void rerunBenchmark()} disabled={benchmarkLoading}>
          <Gauge size={17} weight="fill" />
          <span>{benchmarkLoading ? "压力测试中" : "扩展 Benchmark"}</span>
        </button>
        <button type="button" className="actionChip reportLink" onClick={() => void exportReport()} disabled={reportLoading}>
          <DownloadSimple size={17} weight="fill" />
          <span>{reportLoading ? "导出中" : "导出报告"}</span>
        </button>
      </header>

      <section className="panel">
        <div className="panelTitle">
          <ChartBar size={18} weight="duotone" />
          <h2>六种模式对比</h2>
        </div>
        <div className="evalTable">
          <div className="tableHead">模式</div>
          <div className="tableHead">正常完成</div>
          <div className="tableHead">可恢复完成</div>
          <div className="tableHead">攻击拦截</div>
          <div className="tableHead">硬拒绝</div>
          {rows.map((row) => (
            <div className="evalRow" key={row.mode}>
              <div className="modeCell">{modeLabel(row.mode)}</div>
              <div>
                <span className="mobileLabel">正常完成</span>
                {percent(row.benign_task_completion_rate)}
              </div>
              <div>
                <span className="mobileLabel">可恢复完成</span>
                {percent(row.benign_recoverable_completion_rate ?? row.benign_task_completion_rate)}
              </div>
              <div>
                <span className="mobileLabel">攻击拦截</span>
                {percent(row.attack_interception_rate)}
              </div>
              <div>
                <span className="mobileLabel">硬拒绝</span>
                {percent(row.hard_block_rate ?? row.false_positive_rate)}
              </div>
            </div>
          ))}
        </div>
      </section>

      {benchmark && (
        <section className="panel benchmarkPanel">
          <div className="panelTitle">
            <Gauge size={18} weight="duotone" />
            <h2>工程化 Benchmark</h2>
          </div>
          <div className="benchmarkGrid">
            <div>
              <span>样例执行数</span>
              <strong>{benchmark.basic_benchmark.case_count}</strong>
              <em>唯一模板 {benchmark.basic_benchmark.unique_case_count}；{groupSummary(benchmark.basic_benchmark.n_by_group)}</em>
            </div>
            <div>
              <span>确认降级</span>
              <strong>{percent(agentguardRow(benchmark)?.confirm_rate ?? 0)}</strong>
              <em>用于衡量正常外部分享的人工确认成本</em>
            </div>
            <div>
              <span>一致性审计</span>
              <strong>{ratio(benchmark.consistency_benchmark.consistency_detection_rate, benchmark.consistency_benchmark.abnormal_tool_count)}</strong>
              <em>误报 {ratio(benchmark.consistency_benchmark.consistency_false_positive_rate, benchmark.consistency_benchmark.benign_tool_count)}</em>
            </div>
            <div>
              <span>一致性门控</span>
              <strong>{percent(benchmark.consistency_enforcement?.abnormal_preexecution_block_rate ?? 0)}</strong>
              <em>可选 precheck，异常工具执行前阻断</em>
            </div>
            <div>
              <span>串行压测 P95</span>
              <strong>{benchmark.pressure_test.p95_latency_ms.toFixed(1)}ms</strong>
              <em>{benchmark.pressure_test.iterations} 次，审计 {benchmark.pressure_test.audit_event_count} 条</em>
            </div>
            <div>
              <span>并发吞吐</span>
              <strong>{benchmark.concurrent_pressure_test.throughput_per_sec.toFixed(1)}/s</strong>
              <em>{benchmark.concurrent_pressure_test.workers} workers，P95 {benchmark.concurrent_pressure_test.p95_latency_ms.toFixed(1)}ms</em>
            </div>
          </div>
        </section>
      )}

      <section className="panel highlightPanel">
        <div className="panelTitle">
          <ShieldWarning size={18} weight="duotone" />
          <h2>假设对应关系</h2>
        </div>
        <div className="hypothesisGrid">
          <span>假设一</span>
          <p>{data.baseline.hypotheses.H1 ?? "良性任务完成率对比仅人工确认基线。"}</p>
          <span>假设二</span>
          <p>{data.baseline.hypotheses.H2 ?? "污点状态约束降低二次危险调用。"}</p>
          <span>假设三四</span>
          <p>{data.baseline.hypotheses.H3 ?? "三方一致性审计突出真实运行证据。"}</p>
        </div>
      </section>
    </section>
  );
}

function ratio(rate: number, denominator: number) {
  return `${Math.round(rate * denominator)}/${denominator}`;
}

function percent(rate: number) {
  return `${Math.round(rate * 100)}%`;
}

function modeLabel(mode: string) {
  return {
    no_guard: "无防护",
    approval_only: "仅人工确认",
    rule_only: "仅规则引擎",
    agentguard_minus_taint: "去掉污点控制",
    agentguard_minus_consistency: "去掉一致性审计",
    agentguard: "本系统",
  }[mode] ?? mode;
}

function groupSummary(groups: Record<string, number>) {
  return Object.entries(groups)
    .map(([group, count]) => `${group}:${count}`)
    .join(" / ");
}

function agentguardRow(benchmark: BenchmarkResult) {
  return benchmark.basic_benchmark.rows.find((row) => row.mode === "agentguard");
}
