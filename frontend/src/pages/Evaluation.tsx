import React from "react";
import { ChartBar, Play, ShieldWarning } from "@phosphor-icons/react";
import { useDemo } from "../context/DemoContext";
import { runEvaluation } from "../api/liveDemo";

export function Evaluation() {
  const { data } = useDemo();
  const [loading, setLoading] = React.useState(false);
  const [rows, setRows] = React.useState(data.baseline.rows);

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
      </header>

      <section className="panel">
        <div className="panelTitle">
          <ChartBar size={18} weight="duotone" />
          <h2>六种模式对比</h2>
        </div>
        <div className="evalTable">
          <div className="tableHead">模式</div>
          <div className="tableHead">正常完成</div>
          <div className="tableHead">攻击拦截</div>
          <div className="tableHead">误报</div>
          {rows.map((row) => (
            <div className="evalRow" key={row.mode}>
              <div className="modeCell">{modeLabel(row.mode)}</div>
              <div>
                <span className="mobileLabel">正常完成</span>
                {ratio(row.benign_task_completion_rate, 2)}
              </div>
              <div>
                <span className="mobileLabel">攻击拦截</span>
                {ratio(row.attack_interception_rate, 3)}
              </div>
              <div>
                <span className="mobileLabel">误报</span>
                {ratio(row.false_positive_rate, 2)}
              </div>
            </div>
          ))}
        </div>
      </section>

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
