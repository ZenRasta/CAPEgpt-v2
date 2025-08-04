import { Link, NavLink } from 'react-router-dom';

export default function Navbar() {
  const link = ({ isActive }) =>
    `px-3 py-2 rounded-full hover:bg-white/10 transition ${isActive ? 'bg-white/10' : ''}`;

  return (
    <header className="bg-brand-blue text-white sticky top-0 z-40 shadow-md">
      <div className="container flex items-center justify-between h-16">
        <Link to="/" className="text-xl font-extrabold tracking-tightish">CAPE·GPT 🚀</Link>
        <nav aria-label="main" className="flex items-center gap-2">
          <NavLink to="/" className={link}>Home 🏠</NavLink>
          <NavLink to="/upload" className={link}>Upload 📸</NavLink>
          <NavLink to="/popular" className={link}>Popular 🔥</NavLink>
          <NavLink to="/scoreboard" className={link}>Scoreboard 🏆</NavLink>
        </nav>
      </div>
    </header>
  );
}