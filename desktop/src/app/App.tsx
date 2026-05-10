import { useState } from "react";

import { Sidebar } from "../components/Sidebar";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { navigationItems, type NavigationKey } from "./navigation";

export function App() {
  const [activeView, setActiveView] = useState<NavigationKey>("dashboard");

  return (
    <div className="app-shell">
      <Sidebar
        activeView={activeView}
        items={navigationItems}
        onChange={setActiveView}
      />
      <main className="main-panel">
        {activeView === "dashboard" ? (
          <DashboardPage />
        ) : (
          <section className="placeholder-view">
            <p className="section-label">Modulo preparado</p>
            <h1>{navigationItems.find((item) => item.key === activeView)?.label}</h1>
            <p>
              Esta seccion queda reservada para las siguientes fases del flujo
              local-first.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
