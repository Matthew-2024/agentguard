import React from "react";
import {
  CheckCircle,
  Database,
  Hourglass,
  Play,
  Pulse,
  ShieldCheck,
  Warning,
  WarningCircle,
} from "@phosphor-icons/react";
import { useDemo } from "../context/DemoContext";

const taintLabels = {
  trusted: "可信",
  untrusted: "不可信",
  tainted: "已污染",
  quarantined: "已隔离",
} as const;

export function Dashboard() {
  const { data, status, error, run } = useDemo();
  const taintCounts = React.useMemo(() => aggregateTaintCounts(data.events, data.taint_counts), [data.events, data.taint_counts]);
  const dashboardMetrics = React.useMemo(() => aggregateMetrics(data.events, data.metrics), [data.events, data.metrics]);
  const totalTaint = Object.values(taintCounts).reduce((sum, value) => sum + value, 0) || 1;
  const latestEvents = data.events.slice(0, 3);
  const isLoading = status === "loading";
  const isOffline = status === "offline";
  const isEmpty = data.scenario_runs.every((scenario) => scenario.steps.length === 0);

  return (
    <section className="pageStack">
      <header className="pageHeader">
        <div>
          <p className="eyebrow">运行时网关</p>
          <h1>安全控制台</h1>
        </div>
        <div className="healthPill">
          {isOffline ? <WarningCircle size={18} weight="duotone" /> : <CheckCircle size={18} weight="duotone" />}
          <span>{isOffline ? "后端未连接" : isLoading ? "正在回放真实链路" : "审计日志已同步"}</span>
        </div>
      </header>

      <div className="stateSwitch" aria-label="控制台状态预览">
        <button type="button" className="stateChip active actionChip" onClick={() => void run()} disabled={isLoading}>
          <Play size={17} weight="fill" />
          <span>{isLoading ? "正在运行" : "运行真实演示"}</span>
        </button>
        <span className="sessionChip">会话 {data.session_id}</span>
        <span className="sessionChip">最终状态 {taintLabels[data.final_taint as keyof typeof taintLabels] ?? data.final_taint}</span>
      </div>

      {isLoading && <LoadingState />}
      {isEmpty && !isLoading && <EmptyState />}
      {isOffline && !isLoading && <OfflineState error={error} />}

      {!isLoading && !isEmpty && <div className="metricStrip">
        {dashboardMetrics.map((metric) => (
          <article className="metricItem" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <em className={metric.status}>{metric.trend}</em>
          </article>
        ))}
      </div>}

      <div className={!isLoading && !isOffline ? "twoColumn" : "twoColumn mutedPreview"}>
        <section className="panel">
          <div className="panelTitle">
            <ShieldCheck size={18} weight="duotone" />
            <h2>污点状态分布</h2>
          </div>
          <div className="taintBars">
            {Object.entries(taintCounts).map(([key, count]) => (
              <div className="taintRow" key={key}>
                <span>{taintLabels[key as keyof typeof taintLabels]}</span>
                <div className="barTrack">
                  <div
                    className={`barFill ${key}`}
                    style={{ width: `${Math.max(7, Math.round((count / totalTaint) * 100))}%` }}
                  />
                </div>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panelTitle">
            <Pulse size={18} weight="duotone" />
            <h2>最新安全决策</h2>
          </div>
          <div className="eventList">
            {latestEvents.map((event) => (
              <EventLine
                key={`${event.id}-${event.event_label}`}
                icon={event.decision === "deny" ? <Warning size={16} weight="duotone" /> : <Database size={16} weight="duotone" />}
                title={event.display_name}
                meta={`${event.event_label}：${event.decision_label}`}
              />
            ))}
            {latestEvents.length === 0 && (
              <EventLine
                icon={<ShieldCheck size={16} weight="duotone" />}
                title="等待演示"
                meta="运行真实演示后显示审计事件"
              />
            )}
          </div>
        </section>
      </div>
    </section>
  );
}

function aggregateTaintCounts(
  events: Array<{ taint_after: string | null }>,
  fallback: Record<"trusted" | "untrusted" | "tainted" | "quarantined", number>,
) {
  const counts = { trusted: 0, untrusted: 0, tainted: 0, quarantined: 0 };
  for (const event of events) {
    if (event.taint_after && event.taint_after in counts) {
      counts[event.taint_after as keyof typeof counts] += 1;
    }
  }
  return Object.values(counts).some(Boolean) ? counts : fallback;
}

function aggregateMetrics(
  events: Array<{ decision: string | null; event_type: string }>,
  fallback: Array<{ label: string; value: string; trend: string; status: "success" | "neutral" | "danger" }>,
) {
  if (!events.length) {
    return fallback;
  }
  const blocked = events.filter((event) => event.decision === "deny").length;
  const quarantined = events.filter((event) => event.decision === "quarantine").length;
  const runtime = events.filter((event) => event.event_type === "runtime_evidence").length;
  const transitions = events.filter((event) => event.event_type === "taint_transition").length;
  return [
    { label: "攻击拦截", value: String(blocked + quarantined), trend: "来自审计日志", status: "success" as const },
    { label: "运行证据", value: String(runtime), trend: "代理实时采集", status: "neutral" as const },
    { label: "真实阻断", value: String(blocked), trend: "策略引擎输出", status: blocked ? "danger" as const : "neutral" as const },
    { label: "状态流转", value: String(transitions), trend: "会话级污点记录", status: transitions ? "danger" as const : "success" as const },
  ];
}

function EventLine({ icon, title, meta }: { icon: React.ReactNode; title: string; meta: string }) {
  return (
    <div className="eventLine">
      <div className="eventIcon">{icon}</div>
      <strong>{title}</strong>
      <span>{meta}</span>
    </div>
  );
}

function LoadingState() {
  return (
    <section className="statusPanel" aria-live="polite">
      <Hourglass size={20} weight="duotone" />
      <div>
        <strong>正在回放审计链路</strong>
        <span>系统正在把运行时证据合并到当前调用时间线。</span>
      </div>
      <div className="skeletonStack" aria-hidden="true">
        <i />
        <i />
        <i />
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <section className="statusPanel">
      <Database size={20} weight="duotone" />
      <div>
        <strong>当前会话还没有工具调用</strong>
        <span>运行一个演示剧本后，这里会显示污点变化和运行证据。</span>
      </div>
    </section>
  );
}

function OfflineState({ error }: { error: string | null }) {
  return (
    <section className="statusPanel dangerPanel" role="status">
      <WarningCircle size={20} weight="duotone" />
      <div>
        <strong>安全网关暂时离线</strong>
        <span>{error ? `当前展示离线快照，原因：${error}` : "当前页面展示的是最后一次已验证的审计快照。"}</span>
      </div>
    </section>
  );
}
