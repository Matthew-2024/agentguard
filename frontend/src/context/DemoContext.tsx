import React from "react";
import { fallbackDemo, LiveDemo, loadVerifiedDemo } from "../api/liveDemo";

type DemoContextValue = {
  data: LiveDemo;
  status: "ready" | "loading" | "offline";
  error: string | null;
  run: () => Promise<void>;
};

const DemoContext = React.createContext<DemoContextValue | null>(null);

export function DemoProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = React.useState<LiveDemo>(fallbackDemo);
  const [status, setStatus] = React.useState<DemoContextValue["status"]>("loading");
  const [error, setError] = React.useState<string | null>(null);

  const run = React.useCallback(async () => {
    setStatus("loading");
    setError(null);
    try {
      const live = await loadVerifiedDemo();
      setData(live);
      setStatus("ready");
    } catch (err) {
      setData(fallbackDemo);
      setStatus("offline");
      setError(err instanceof Error ? err.message : "无法连接后端演示接口");
    }
  }, []);

  React.useEffect(() => {
    void run();
  }, [run]);

  const value = React.useMemo(() => ({ data, status, error, run }), [data, error, run, status]);

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}

export function useDemo() {
  const context = React.useContext(DemoContext);
  if (!context) {
    throw new Error("useDemo must be used inside DemoProvider");
  }
  return context;
}
