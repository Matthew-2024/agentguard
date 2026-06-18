import React from "react";
import ReactDOM from "react-dom/client";
import { ShieldCheck } from "@phosphor-icons/react";
import { Dashboard } from "./pages/Dashboard";
import { CallChain } from "./pages/CallChain";
import { ToolAudit } from "./pages/ToolAudit";
import { Evaluation } from "./pages/Evaluation";
import { DemoProvider, useDemo } from "./context/DemoContext";
import "@fontsource/geist-sans/400.css";
import "@fontsource/geist-sans/500.css";
import "@fontsource/geist-sans/600.css";
import "@fontsource/geist-sans/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/600.css";
import "./styles/app.css";

const pages = [
  { id: "dashboard", label: "总览", component: <Dashboard /> },
  { id: "call-chain", label: "调用链", component: <CallChain /> },
  { id: "tool-audit", label: "工具审计", component: <ToolAudit /> },
  { id: "evaluation", label: "评测结果", component: <Evaluation /> },
];

function App() {
  const [activePage, setActivePage] = React.useState(pages[0].id);
  const current = pages.find((page) => page.id === activePage) ?? pages[0];
  const { status } = useDemo();

  return (
    <div className="appShell">
      <aside className="sidebar" aria-label="智能体安全控制台栏目">
        <div className="brand">
          <div className="brandMark" aria-hidden="true">
            <ShieldCheck size={22} weight="duotone" />
          </div>
          <div>
            <strong>智能体安全控制台</strong>
            <span>工具调用链防护</span>
          </div>
        </div>
        <nav className="navList">
          {pages.map((page) => (
            <button
              key={page.id}
              type="button"
              className={page.id === current.id ? "navItem active" : "navItem"}
              onClick={() => setActivePage(page.id)}
            >
              {page.label}
            </button>
          ))}
        </nav>
        <div className="sidebarMeta">
          <span>运行状态</span>
          <strong>{status === "ready" ? "真实回放已同步" : status === "loading" ? "正在回放" : "离线快照"}</strong>
        </div>
      </aside>
      <main className="mainPanel">{current.component}</main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <DemoProvider>
      <App />
    </DemoProvider>
  </React.StrictMode>,
);
