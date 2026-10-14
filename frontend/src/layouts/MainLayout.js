import { Link, NavLink, useLocation } from "react-router-dom";
import { useState } from "react";
import "../App.css";

const LINKS = [
  { to: "/", label: "Dashboard", icon: "[D]" },
  { to: "/analytics", label: "Analytics", icon: "[A]" },
  { to: "/buildings", label: "Buildings", icon: "[B]" },
  { to: "/ai-insights", label: "AI Insights", icon: "[*]" },
  { to: "/issues", label: "Issues", icon: "[!]" },
  { to: "/reports", label: "Reports", icon: "[R]" },
];

export default function MainLayout({ children }) {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  return (
    <div className="shell">
      <aside className={"sidebar" + (open ? " open" : "")}>
        <Link to="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark">O</span>
          <span>
            <strong>EcoPulse</strong>
            <small>Campus Resource Intelligence</small>
          </span>
        </Link>
        <nav className="nav">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
            >
              <span className="nav-icon">{l.icon}</span> {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="side-foot">
          <span className="dot live" /> API: {process.env.REACT_APP_RESOURCE_URL || "localhost:5001"}
          <br />
          <span className="dot ai" /> AI: {process.env.REACT_APP_AI_URL || "localhost:5002"}
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <button className="hamburger" onClick={() => setOpen((o) => !o)} aria-label="Menu">
            ☰
          </button>
          <div className="crumb">{pathTitle(loc.pathname)}</div>
          <div className="top-right">
            <span className="pill">Green Campus</span>
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}

function pathTitle(p) {
  const found = LINKS.find((l) => l.to === p || (l.to !== "/" && p.indexOf(l.to) === 0));
  return found ? found.label : "EcoPulse";
}
