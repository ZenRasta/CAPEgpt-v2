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
        className={`gen-glass-card p-6 ${className}`}
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
    <div className={`gen-glass-card p-6 ${className}`} {...props}>
      {children}
    </div>
  );
};

export const GlassButton = ({ 
  children, 
  variant = 'primary', 
  className = '', 
  onClick,
  ...props 
}) => {
  const baseClass = `gen-button ${variant === 'primary' ? 'gen-button-primary' : 'gen-button-secondary'}`;

  return (
    <motion.button
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