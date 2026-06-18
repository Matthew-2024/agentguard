import {
  ArrowRight,
  Detective,
  FileLock,
  GlobeHemisphereWest,
  LockKey,
  Prohibit,
  Robot,
} from "@phosphor-icons/react";
import React from "react";
import { useDemo } from "../context/DemoContext";

export function CallChain() {
  const { data } = useDemo();
  const traceEvents = data.events
    .filter((event) => ["precheck", "postcheck", "taint_transition"].includes(event.event_type))
    .slice(0, 4);
  const steps = traceEvents.length
    ? [...traceEvents].reverse().map((event) => ({
      title: event.display_name,
      meta: traceSummary(event),
      state: event.decision === "deny" ? "denied" : event.taint_after ?? event.taint_before ?? "trusted",
      score: event.decision === "deny" ? "拒绝" : taintLabel(event.taint_after ?? event.taint_before),
      icon: iconForStep(event.tool_name ?? "", event.decision ?? ""),
    }))
    : [
      {
        title: "等待演示",
        meta: "运行真实演示后显示审计事件",
        state: "trusted",
        score: "可信",
        icon: <Robot size={20} weight="duotone" />,
      },
    ];

  return (
    <section className="pageStack">
      <header className="pageHeader">
        <div>
          <p className="eyebrow">污点传播</p>
          <h1>调用链状态流转</h1>
        </div>
      </header>

      <div className="riskPath" aria-label="污点传播路径">
        {steps.map((step, index) => (
          <div className="pathStage" key={step.title} style={{ "--index": index } as React.CSSProperties}>
            <article className={`chainNode ${step.state}`}>
              <div className="nodeIcon">{step.icon}</div>
              <strong>{step.title}</strong>
              <span>{step.meta}</span>
              <b>{step.score}</b>
            </article>
            {index < steps.length - 1 && (
              <div className="chainArrow">
                <ArrowRight size={22} weight="bold" />
              </div>
            )}
          </div>
        ))}
      </div>

      <section className="panel">
        <div className="panelTitle">
          <FileLock size={18} weight="duotone" />
          <h2>审计轨迹</h2>
        </div>
        <div className="traceTable">
          {traceEvents.slice(0, 2).map((event) => (
            <React.Fragment key={`${event.id}-${event.event_label}`}>
              <div>{event.event_label}</div>
              <div>{event.display_name}：{traceSummary(event)}</div>
              <strong>{event.decision_label}</strong>
            </React.Fragment>
          ))}
        </div>
      </section>
    </section>
  );
}

function iconForStep(toolName: string, decision: string) {
  if (decision === "deny") {
    return toolName === "send_external" ? <Prohibit size={20} weight="duotone" /> : <LockKey size={20} weight="duotone" />;
  }
  if (toolName === "search_api") {
    return <GlobeHemisphereWest size={20} weight="duotone" />;
  }
  if (toolName.includes("weather")) {
    return <Detective size={20} weight="duotone" />;
  }
  return <Robot size={20} weight="duotone" />;
}

function traceSummary(event: { metadata: Record<string, unknown>; taint_after: string | null }) {
  const poison = event.metadata.poison as { reasoning?: string } | null | undefined;
  if (poison?.reasoning) {
    return poison.reasoning;
  }
  if (typeof event.metadata.rule_matched === "string") {
    return event.metadata.rule_matched;
  }
  if (typeof event.metadata.reason === "string") {
    return event.metadata.reason;
  }
  return event.taint_after ? `状态变为 ${event.taint_after}` : "运行时证据已记录";
}

function taintLabel(status?: string | null) {
  return {
    trusted: "可信",
    untrusted: "不可信",
    tainted: "已污染",
    quarantined: "已隔离",
  }[status ?? ""] ?? "可信";
}
