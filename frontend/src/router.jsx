import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthProvider';
import Layout from './components/Layout';
import Login from './pages/Login';
import Home from './pages/Home';
import UploadQA from './pages/UploadQA';
import QuestionViewer from './components/QuestionViewer';
import Settings from './pages/Settings';
import { GlassCard, GlassButton } from './components/GlassCard';
import { motion } from 'framer-motion';
import FullPageSpinner from './components/FullPageSpinner';

// Protected route wrapper
const Protected = ({ children }) => {
  const { session, loading } = useAuth();
  
  if (loading) {
    return <FullPageSpinner />;
  }
  
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  
  return <Layout>{children}</Layout>;
};

// Popular Questions Component
function Popular() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2
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

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="py-8"
    >
      <section className="container mx-auto px-4">
        <motion.h1 
          className="text-5xl md:text-6xl font-extrabold mb-12 text-center bg-accent-gradient bg-clip-text text-transparent tracking-tight"
          animate={{ 
            textShadow: [
              "0 0 20px rgba(255, 93, 162, 0.5)",
              "0 0 40px rgba(179, 255, 56, 0.5)",
              "0 0 20px rgba(255, 93, 162, 0.5)"
            ]
          }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        >
          🔥 TOP POPULAR QUESTIONS 🌟
        </motion.h1>
        
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
          variants={containerVariants}
        >
          {[
            { emoji: "🧮", title: "SOLVE ∫X³DX", count: "1,234", color: "text-electric-cyan" },
            { emoji: "⚡", title: "NEWTON'S SECOND LAW", count: "987", color: "text-lime-slush" },
            { emoji: "📊", title: "QUADRATIC EQUATION ROOTS", count: "856", color: "text-bubblegum-pink" },
            { emoji: "📐", title: "TRIGONOMETRIC IDENTITIES", count: "743", color: "text-hyper-violet" },
            { emoji: "⚛️", title: "ATOMIC STRUCTURE", count: "612", color: "text-electric-cyan" },
            { emoji: "🔬", title: "ORGANIC CHEMISTRY", count: "589", color: "text-lime-slush" }
          ].map((item, index) => (
            <motion.div key={index} variants={cardVariants}>
              <GlassCard className="text-center p-8 hover:scale-105 transition-transform">
                <div className="text-5xl mb-4">{item.emoji}</div>
                <h3 className={`text-xl font-bold mb-4 ${item.color} tracking-wide`}>
                  {item.title}
                </h3>
                <p className="text-white/70 mb-4 text-sm">Asked {item.count} times</p>
                <GlassButton variant="secondary" className="font-bold tracking-wide">
                  VIEW SOLUTION ✨
                </GlassButton>
              </GlassCard>
            </motion.div>
          ))}
        </motion.div>
      </section>
    </motion.div>
  );
}

// Scoreboard Component
function Scoreboard() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.3
      }
    }
  };

  const sectionVariants = {
    hidden: { opacity: 0, x: -30 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { 
        duration: 0.6,
        ease: "easeOut"
      }
    }
  };

  const students = [
    { name: "JOHN D.", icon: "🔥", points: "950", rank: 1, color: "text-lime-slush" },
    { name: "SARAH K.", icon: "💪", points: "920", rank: 2, color: "text-electric-cyan" },
    { name: "MICHAEL T.", icon: "🌟", points: "890", rank: 3, color: "text-bubblegum-pink" },
    { name: "EMMA L.", icon: "⚡", points: "875", rank: 4, color: "text-hyper-violet" },
    { name: "ALEX R.", icon: "🚀", points: "840", rank: 5, color: "text-lime-slush" }
  ];

  const schools = [
    { name: "ST. MARY'S COLLEGE", icon: "📚", points: "2500", rank: 1, color: "text-lime-slush" },
    { name: "HILLVIEW COLLEGE", icon: "🏆", points: "2300", rank: 2, color: "text-electric-cyan" },
    { name: "PRESENTATION COLLEGE", icon: "⭐", points: "2100", rank: 3, color: "text-bubblegum-pink" },
    { name: "QUEENS ROYAL COLLEGE", icon: "👑", points: "1950", rank: 4, color: "text-hyper-violet" },
    { name: "FATIMA COLLEGE", icon: "🌟", points: "1820", rank: 5, color: "text-lime-slush" }
  ];

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="py-8"
    >
      <section className="container mx-auto px-4">
        <motion.h1 
          className="text-5xl md:text-6xl font-extrabold mb-12 text-center bg-accent-gradient bg-clip-text text-transparent tracking-tight"
          animate={{ 
            textShadow: [
              "0 0 20px rgba(145, 70, 255, 0.5)",
              "0 0 40px rgba(35, 240, 255, 0.5)",
              "0 0 20px rgba(145, 70, 255, 0.5)"
            ]
          }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        >
          🏆 LEADERBOARDS 🥇
        </motion.h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <motion.div variants={sectionVariants}>
            <h2 className="text-3xl font-bold mb-8 text-center bg-accent-gradient bg-clip-text text-transparent tracking-wide">
              TOP STUDENTS <span aria-hidden="true">🌟</span>
            </h2>
            <GlassCard className="p-8">
              <div className="space-y-6">
                {students.map((student, index) => (
                  <motion.div 
                    key={student.name}
                    className="flex items-center justify-between p-4 rounded-panel backdrop-blur-lg bg-panel-gradient border border-white/20 shadow-glass hover:shadow-glass-hover hover:scale-102 transition-transform"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="flex items-center space-x-4">
                      <span className="text-2xl font-bold text-white/60">#{student.rank}</span>
                      <span className="text-2xl">{student.icon}</span>
                      <span className={`font-bold text-lg tracking-wide ${student.color}`}>{student.name}</span>
                    </div>
                    <span className="font-bold text-xl text-white">{student.points} PTS</span>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </motion.div>

          <motion.div variants={sectionVariants}>
            <h2 className="text-3xl font-bold mb-8 text-center bg-accent-gradient bg-clip-text text-transparent tracking-wide">
              TOP SCHOOLS <span aria-hidden="true">🏫</span>
            </h2>
            <GlassCard className="p-8">
              <div className="space-y-6">
                {schools.map((school, index) => (
                  <motion.div 
                    key={school.name}
                    className="flex items-center justify-between p-4 rounded-panel backdrop-blur-lg bg-panel-gradient border border-white/20 shadow-glass hover:shadow-glass-hover hover:scale-102 transition-transform"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="flex items-center space-x-4">
                      <span className="text-2xl font-bold text-white/60">#{school.rank}</span>
                      <span className="text-2xl">{school.icon}</span>
                      <span className={`font-bold text-lg tracking-wide ${school.color}`}>{school.name}</span>
                    </div>
                    <span className="font-bold text-xl text-white">{school.points} PTS</span>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        </div>
      </section>
    </motion.div>
  );
}

// App Routes
function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Protected><Home /></Protected>} />
      <Route path="/upload" element={<Protected><UploadQA /></Protected>} />
      <Route path="/question/:id" element={<Protected><QuestionViewer /></Protected>} />
      <Route path="/popular" element={<Protected><Popular /></Protected>} />
      <Route path="/scoreboard" element={<Protected><Scoreboard /></Protected>} />
      <Route path="/settings" element={<Protected><Settings /></Protected>} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default function Router() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}