import { motion } from 'framer-motion';

export const GlassCard = ({ children, className = '', animate = true, ...props }) => {
  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.5,
        ease: "easeOut"
      }
    }
  };

  if (animate) {
    return (
        <motion.div
          className={`rounded-panel backdrop-blur-lg bg-panel-gradient border border-white/20 shadow-glass transition-all p-6 ${className}`}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        whileHover={{ scale: 1.02, y: -4 }}
        whileTap={{ scale: 0.98 }}
        {...props}
      >
        {children}
      </motion.div>
    );
  }

  return (
      <div className={`rounded-panel backdrop-blur-lg bg-panel-gradient border border-white/20 shadow-glass transition-all p-6 ${className}`} {...props}>
      {children}
    </div>
  );
};

export const GlassButton = ({ 
  children, 
  variant = 'primary', 
  className = '', 
  onClick,
  type = 'button',
  ...props 
}) => {
    const baseClass = `rounded-chip px-6 py-3 font-semibold tracking-wide transition-all ${
      variant === 'primary'
        ? 'bg-accent-gradient text-white animate-pulseGlow'
        : 'bg-panel-gradient text-electric-cyan border border-electric-cyan/30 backdrop-blur-lg'
    }`;

  return (
    <motion.button
      type={type}
      className={`${baseClass} ${className}`}
      onClick={onClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
      {...props}
    >
      {children}
    </motion.button>
  );
};

export default GlassCard;