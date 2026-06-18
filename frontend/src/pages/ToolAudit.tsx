import React from "react";
import { ArrowsClockwise, CheckCircle, FileCode, WarningOctagon } from "@phosphor-icons/react";
import { useDemo } from "../context/DemoContext";
import { fetchToolConsistencyReports } from "../api/liveDemo";

export function ToolAudit() {
  const { data } = useDemo();
  const [reports, setReports] = React.useState(data.consistency_reports);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    setReports(data.consistency_reports);
  }, [data.consistency_reports]);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    try {
      const live = await fetchToolConsistencyReports();
      setReports(live.length ? live : data.consistency_reports);
    } finally {
      setLoading(false);
    }
  }, [data.consistency_reports]);

  return (
    <section className="pageStack">
      <header className="pageHeader">
        <div>
          <p className="eyebrow">声明层 · 静态层 · 运行时层</p>
          <h1>工具三方一致性审计</h1>
        </div>
        <button type="button" className="actionChip" onClick={() => void refresh()} disabled={loading}>
          <ArrowsClockwise size={17} weight="bold" />
          <span>{loading ? "刷新中" : "刷新审计"}</span>
        </button>
      </header>

      <section className="panel">
        <div className="panelTitle">
          <FileCode size={18} weight="duotone" />
          <h2>偏差卡片</h2>
        </div>
        <div className="auditGrid">
          {reports.map((tool) => (
            <article className="auditCard" key={tool.tool_name}>
              <div className="auditHead">
                <strong>{tool.display_name}</strong>
                <span className={`riskBadge ${tool.report.risk_level}`}>{riskLabel(tool.report.risk_level)}</span>
              </div>
              <dl>
                <dt>声明</dt>
                <dd>{tool.manifest_summary}</dd>
                <dt>静态</dt>
                <dd>{tool.static_summary}</dd>
                <dt>运行时</dt>
                <dd>{tool.runtime_summary}</dd>
              </dl>
              <div className="scoreLine">
                {tool.report.risk_level === "low" ? <CheckCircle size={16} weight="duotone" /> : <WarningOctagon size={16} weight="duotone" />}
                <span>风险分 {tool.report.consistency_score}</span>
              </div>
              <p className="auditSummary">{tool.report.summary}</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}

function riskLabel(level: string) {
  return {
    low: "低",
    medium: "中",
    high: "高",
    critical: "严重",
  }[level] ?? level;
}
