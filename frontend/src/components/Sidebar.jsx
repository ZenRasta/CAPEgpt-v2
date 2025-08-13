import { Link, NavLink } from 'react-router-dom';

export default function Sidebar() {
  const navItems = [
    { to: '/', label: 'CHAT 💬' },
    { to: '/upload', label: 'UPLOAD 📸' },
    { to: '/popular', label: 'POPULAR 🔥' },
    { to: '/scoreboard?tab=leader', label: 'LEADER 🏆' },
    { to: '/scoreboard?tab=schools', label: 'SCHOOLS 🏫' },
    { to: '/settings', label: 'SETTINGS ⚙️' }
  ];

  return (
    <aside className="w-64 p-4 flex flex-col gap-4">
      <Link
        to="/"
        className="text-3xl font-bold gen-gradient-text tracking-wide"
      >
        CAPE·GPT 🚀
      </Link>

      <Link
        to="/"
        className="bg-electric-cyan text-black font-bold py-2 px-4 rounded-xl text-center hover:bg-electric-cyan/80 transition-colors"
      >
        + New Chat
      </Link>

      <nav className="flex flex-col gap-2">
        {navItems.map((item) => (
          <NavLink
            key={item.label}
            to={item.to}
            className={({ isActive }) =>
              `rounded-xl px-4 py-2 font-semibold transition-colors hover:bg-white/10 ${
                isActive ? 'bg-white/20 text-electric-cyan' : 'text-white'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
