import { Outlet } from "react-router-dom";

import { navigationItems } from "../app/navigation";
import { useHealthCheck } from "../hooks/useHealthCheck";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function AppShell() {
  const healthCheck = useHealthCheck();

  return (
    <div className="app-shell">
      <Sidebar items={navigationItems} />
      <main className="main-panel">
        <TopBar healthCheck={healthCheck} />
        <Outlet context={{ healthCheck }} />
      </main>
    </div>
  );
}
