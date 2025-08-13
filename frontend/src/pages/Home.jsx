import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { GlassCard, GlassButton } from '../components/GlassCard';

export default function Home() {
  const heroVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.8,
        ease: "easeOut"
      }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.6,
        ease: "easeOut"
      }
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2
      }
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Hero Section */}
      <section className="relative py-20 px-4 overflow-hidden">
        {/* Background gradient effects */}
        <div className="absolute inset-0 bg-gradient-to-br from-hyper-violet/20 via-bubblegum-pink/20 to-electric-cyan/20 blur-3xl" />
        <div className="absolute top-10 left-10 w-72 h-72 bg-lime-slush/10 rounded-full blur-2xl" />
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-electric-cyan/10 rounded-full blur-2xl" />
        
        <motion.div 
          className="container mx-auto text-center relative z-10"
          variants={heroVariants}
        >
            <motion.h1
              className="text-6xl md:text-7xl font-extrabold mb-6 bg-accent-gradient bg-clip-text text-transparent tracking-tight"
            animate={{ 
              textShadow: [
                "0 0 20px rgba(35, 240, 255, 0.5)",
                "0 0 40px rgba(145, 70, 255, 0.5)",
                "0 0 20px rgba(35, 240, 255, 0.5)"
              ]
            }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            YOUR AI BUDDY FOR CAPE EXAMS! 💥
          </motion.h1>
          
          <motion.p 
            className="text-xl md:text-2xl mb-8 text-white/90 font-medium tracking-wide"
            variants={heroVariants}
          >
            SNAP QUESTIONS, GET LIT SOLUTIONS, AND LEVEL UP YOUR GAME! 🎮
          </motion.p>

          <motion.div variants={heroVariants}>
            <GlassButton variant="primary" className="text-xl px-12 py-4 font-bold">
              <Link to="/upload">LET'S GO! 🚀</Link>
            </GlassButton>
          </motion.div>
        </motion.div>
      </section>

      {/* Quick Examples */}
      <section className="container mx-auto px-4 py-16">
          <motion.h2
            className="text-4xl md:text-5xl font-bold mb-12 text-center bg-accent-gradient bg-clip-text text-transparent tracking-wide"
          variants={heroVariants}
        >
          QUICK VIBES EXAMPLES 🤩
        </motion.h2>
        
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto"
          variants={containerVariants}
        >
          <motion.div variants={cardVariants}>
              <GlassCard className="text-center p-8 hover:scale-105 transition-transform">
                <div className="text-4xl mb-4" aria-hidden="true">📐</div>
              <h3 className="text-xl font-bold mb-4 text-electric-cyan tracking-wide">
                DIFFERENTIATE F(X) = X²Eˣ
              </h3>
              <GlassButton variant="secondary" className="mt-4">
                <Link to="/popular">VIEW SOLUTION ✨</Link>
              </GlassButton>
            </GlassCard>
          </motion.div>

          <motion.div variants={cardVariants}>
              <GlassCard className="text-center p-8 hover:scale-105 transition-transform">
                <div className="text-4xl mb-4" aria-hidden="true">🚀</div>
              <h3 className="text-xl font-bold mb-4 text-lime-slush tracking-wide">
                PROJECTILE MOTION: MAX HEIGHT
              </h3>
              <GlassButton variant="secondary" className="mt-4">
                <Link to="/popular">VIEW SOLUTION ✨</Link>
              </GlassButton>
            </GlassCard>
          </motion.div>
        </motion.div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16">
        <motion.div variants={cardVariants}>
            <GlassCard className="text-center p-12 max-w-2xl mx-auto">
              <motion.div
                className="text-6xl mb-6"
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                aria-hidden="true"
              >
                📸
              </motion.div>
              <h3 className="text-3xl font-bold mb-4 bg-accent-gradient bg-clip-text text-transparent tracking-wide">
              DROP YOUR QUESTION
            </h3>
            <p className="text-lg text-white/80 mb-8 font-medium">
              Snap a past-paper question and we'll analyze it for strengths & weaknesses.
            </p>
            <GlassButton variant="primary" className="text-lg px-8 py-3">
              <Link to="/upload">UPLOAD NOW 📤</Link>
            </GlassButton>
          </GlassCard>
        </motion.div>
      </section>
    </motion.div>
  );
}