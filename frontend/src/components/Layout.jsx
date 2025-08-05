import { motion } from 'framer-motion';
import Navbar from './Navbar';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen text-white">
      <Navbar />
      <motion.main 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
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
            &copy; {new Date().getFullYear()} CAPE·GPT. All rights reserved. Made with ❤️ by <span className="gen-gradient-text font-bold">Gen Alpha Vibes!</span>
          </motion.p>
        </div>
      </footer>
    </div>
  );
}