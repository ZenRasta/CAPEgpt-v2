import { motion } from 'framer-motion';
import Sidebar from './Sidebar';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen text-white flex">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <motion.main
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="flex-1"
        >
          {children}
        </motion.main>
        <footer className="bg-gradient-to-r from-hyper-violet to-bubblegum-pink py-8 mt-20">
          <div className="container mx-auto px-4 text-center">
              <motion.p
                className="text-lg font-semibold"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
                &copy; {new Date().getFullYear()} CAPE·GPT. All rights reserved. Made with ❤️ by <span className="bg-accent-gradient bg-clip-text text-transparent font-bold">Gen Alpha Vibes!</span>
            </motion.p>
          </div>
        </footer>
      </div>
    </div>
  );
}
