import { NavLink } from "react-router-dom";

import type { NavigationItem } from "../app/navigation";

type SidebarProps = {
  items: NavigationItem[];
};

export function Sidebar({ items }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <span className="brand-mark">RCS</span>
        <div>
          <p>Rancho</p>
          <strong>Content Studio</strong>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Navegacion principal">
        {items.map((item) => (
          <NavLink
            className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
            end={item.path === "/"}
            key={item.key}
            to={item.path}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
