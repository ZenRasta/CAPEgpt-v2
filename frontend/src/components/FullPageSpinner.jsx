import { motion } from 'framer-motion';

export default function FullPageSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-hero-radial">
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-electric-cyan border-t-transparent rounded-full mx-auto mb-4"
        />
        <p className="text-white/80 text-lg font-medium tracking-wide">
          Loading...
        </p>
      </div>
    </div>
  );
}