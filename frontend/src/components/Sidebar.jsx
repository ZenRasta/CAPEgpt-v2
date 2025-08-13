import { Link, NavLink } from 'react-router-dom';

export default function Sidebar() {
  const navItems = [
    { to: '/', label: 'CHAT', icon: '💬' },
    { to: '/upload', label: 'UPLOAD', icon: '📸' },
    { to: '/popular', label: 'POPULAR', icon: '🔥' },
    { to: '/scoreboard?tab=leader', label: 'LEADER', icon: '🏆' },
    { to: '/scoreboard?tab=schools', label: 'SCHOOLS', icon: '🏫' },
    { to: '/settings', label: 'SETTINGS', icon: '⚙️' }
  ];

  return (
      <aside className="w-64 p-4 flex flex-col gap-4">
        <Link
          to="/"
          aria-label="CAPE GPT home"
          className="text-3xl font-bold bg-accent-gradient bg-clip-text text-transparent tracking-wide"
        >
          CAPE·GPT <span aria-hidden="true">🚀</span>
        </Link>

        <Link
          to="/"
          aria-label="Start new chat"
          className="bg-electric-cyan text-black font-bold py-2 px-4 rounded-xl text-center hover:bg-electric-cyan/80 transition-colors"
        >
          + New Chat
        </Link>

        <h2 className="sr-only">Main navigation</h2>
        <nav className="flex flex-col gap-2" aria-label="Main">
          {navItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              aria-label={item.label}
              className={({ isActive }) =>
                `rounded-xl px-4 py-2 font-semibold transition-colors hover:bg-white/10 ${
                  isActive ? 'bg-white/20 text-electric-cyan' : 'text-white'
                }`
              }
            >
              {item.label} <span aria-hidden="true">{item.icon}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
  );
}
