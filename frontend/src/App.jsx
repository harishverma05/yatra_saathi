import { useState } from "react";
import Guide from "./Guide.jsx";
import Interpreter from "./Interpreter.jsx";
import Dashboard from "./Dashboard.jsx";

const NAV_ITEMS = [
  { id: "dashboard", icon: "📊", label: "Dashboard" },
  { id: "guide", icon: "🏛️", label: "AI Guide" },
  { id: "interp", icon: "🌐", label: "Interpreter" },
];

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const pageTitle = NAV_ITEMS.find((n) => n.id === tab)?.label || "Dashboard";

  return (
    <div className="dashboard">
      {/* Sidebar overlay for mobile */}
      <div
        className={`sidebar-overlay ${sidebarOpen ? "open" : ""}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <h1>यात्रा साथी</h1>
          <span>AI Travel Companion</span>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${tab === item.id ? "active" : ""}`}
              onClick={() => {
                setTab(item.id);
                setSidebarOpen(false);
              }}
            >
              <span className="icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="status-badge">
            <span className="dot" />
            System Online
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="main-content">
        <header className="topbar">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button className="hamburger" onClick={() => setSidebarOpen(!sidebarOpen)}>
              ☰
            </button>
            <span className="topbar-title">{pageTitle}</span>
          </div>
          <div className="topbar-actions">
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Lucknow, India</span>
          </div>
        </header>

        <div className="page" key={tab}>
          {tab === "dashboard" && <Dashboard onNavigate={setTab} />}
          {tab === "guide" && <Guide />}
          {tab === "interp" && <Interpreter />}
        </div>
      </div>
    </div>
  );
}
