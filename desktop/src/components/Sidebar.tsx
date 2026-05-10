import type { NavigationItem, NavigationKey } from "../app/navigation";

type SidebarProps = {
  activeView: NavigationKey;
  items: NavigationItem[];
  onChange: (view: NavigationKey) => void;
};

export function Sidebar({ activeView, items, onChange }: SidebarProps) {
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
          <button
            className={item.key === activeView ? "nav-item active" : "nav-item"}
            key={item.key}
            onClick={() => onChange(item.key)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
