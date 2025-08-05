import { motion } from 'framer-motion';
import { Link, NavLink } from 'react-router-dom';

export default function Navbar() {
  const navVariants = {
    hidden: { opacity: 0, y: -20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.5,
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: -20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <motion.header 
      className="gen-glass-card sticky top-4 z-50 mx-4 mb-8"
      variants={navVariants}
      initial="hidden"
      animate="visible"
    >
      <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
        <motion.h1 
          className="text-3xl font-bold gen-gradient-text tracking-wide"
          variants={itemVariants}
        >
          <Link to="/" className="hover:scale-105 transition-transform">
            CAPE·GPT 🚀
          </Link>
        </motion.h1>
        
        <motion.ul 
          className="flex space-x-6"
          variants={navVariants}
        >
          <motion.li variants={itemVariants}>
            <NavLink 
              to="/" 
              className={({ isActive }) => 
                `px-4 py-2 rounded-full font-semibold tracking-wide transition-all hover:text-electric-cyan hover:bg-white/10 ${
                  isActive ? 'text-electric-cyan bg-white/10' : 'text-white/90'
                }`
              }
            >
              HOME 🏠
            </NavLink>
          </motion.li>
          <motion.li variants={itemVariants}>
            <NavLink 
              to="/upload" 
              className={({ isActive }) => 
                `px-4 py-2 rounded-full font-semibold tracking-wide transition-all hover:text-lime-slush hover:bg-white/10 ${
                  isActive ? 'text-lime-slush bg-white/10' : 'text-white/90'
                }`
              }
            >
              UPLOAD 📸
            </NavLink>
          </motion.li>
          <motion.li variants={itemVariants}>
            <NavLink 
              to="/popular" 
              className={({ isActive }) => 
                `px-4 py-2 rounded-full font-semibold tracking-wide transition-all hover:text-bubblegum-pink hover:bg-white/10 ${
                  isActive ? 'text-bubblegum-pink bg-white/10' : 'text-white/90'
                }`
              }
            >
              POPULAR 🔥
            </NavLink>
          </motion.li>
          <motion.li variants={itemVariants}>
            <NavLink 
              to="/scoreboard" 
              className={({ isActive }) => 
                `px-4 py-2 rounded-full font-semibold tracking-wide transition-all hover:text-hyper-violet hover:bg-white/10 ${
                  isActive ? 'text-hyper-violet bg-white/10' : 'text-white/90'
                }`
              }
            >
              SCOREBOARD 🏆
            </NavLink>
          </motion.li>
        </motion.ul>
      </nav>
    </motion.header>
  );
}