import { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthProvider';
import { Navigate } from 'react-router-dom';
import { SiGoogle } from 'react-icons/si';

function Login() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { session, loginGuest, signInWithGoogle } = useAuth();

  // Redirect if already authenticated
  if (session) {
    return <Navigate to="/" replace />;
  }

  const handleGoogleSignIn = async () => {
    try {
      setLoading(true);
      setError(null);
      await signInWithGoogle();
    } catch (err) {
      setError('Failed to sign in with Google. Please try again.');
      console.error('Google sign in error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGuestMode = () => {
    try {
      loginGuest();
    } catch (err) {
      setError('Failed to continue as guest. Please try again.');
      console.error('Guest mode error:', err);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-hero-radial p-4">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-hyper-violet/20 via-bubblegum-pink/20 to-electric-cyan/20 blur-3xl" />
      <div className="absolute top-20 left-20 w-96 h-96 bg-lime-slush/10 rounded-full blur-2xl" />
      <div className="absolute bottom-20 right-20 w-72 h-72 bg-electric-cyan/10 rounded-full blur-2xl" />
      
      {/* Background Google Logo */}
      <SiGoogle className="absolute -z-10 opacity-10 w-[300px] h-[300px] top-10 right-10 pointer-events-none text-white" />
      
      <motion.div 
        className="w-full max-w-md space-y-8 rounded-3xl backdrop-blur-xl bg-white/5 p-10 ring-1 ring-white/20 relative z-10"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Header */}
        <div className="text-center mb-8">
            <motion.h1
              className="text-4xl font-extrabold bg-accent-gradient bg-clip-text text-transparent mb-4 tracking-tight"
            animate={{ 
              textShadow: [
                "0 0 20px rgba(35, 240, 255, 0.5)",
                "0 0 40px rgba(145, 70, 255, 0.5)",
                "0 0 20px rgba(35, 240, 255, 0.5)"
              ]
            }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            WELCOME TO CAPE·GPT! 🚀
          </motion.h1>
          <p className="text-white/80 text-lg font-medium tracking-wide">
            YOUR AI BUDDY FOR CAPE EXAMS
          </p>
        </div>

        {/* Error Message */}
        {error && (
            <motion.div
              className="mb-6 p-4 rounded-panel backdrop-blur-lg bg-panel-gradient border border-red-400/30 shadow-glass"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <p className="text-red-200 text-sm font-medium text-center">
              {error}
            </p>
          </motion.div>
        )}

        {/* Auth Buttons */}
        <div className="space-y-4">
          {/* Google OAuth Button */}
            <motion.button
              onClick={handleGoogleSignIn}
              disabled={loading}
              aria-label="Continue with Google"
              className="w-full flex items-center justify-center gap-3 rounded-panel bg-accent-gradient text-white font-bold tracking-wide py-4 px-6 transition-all hover:scale-102 active:scale-98"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-6 h-6 border-2 border-electric-cyan border-t-transparent rounded-full"
                  aria-hidden="true"
                />
              ) : (
                <>
                  <SiGoogle className="w-6 h-6" aria-hidden="true" />
                  <span className="font-bold text-white tracking-wide">CONTINUE WITH GOOGLE</span>
                </>
              )}
            </motion.button>

        </div>

        {/* Divider */}
        <div className="my-8 flex items-center">
          <div className="flex-1 border-t border-white/20"></div>
          <span className="px-4 text-sm text-white/60 font-medium tracking-wide">OR</span>
          <div className="flex-1 border-t border-white/20"></div>
        </div>

        {/* Guest Mode */}
          <button
            onClick={handleGuestMode}
            aria-label="Continue as guest"
            className="w-full flex items-center justify-center gap-3 rounded-panel bg-panel-gradient text-electric-cyan border border-electric-cyan/30 backdrop-blur-lg font-bold tracking-wide py-4 px-6 transition-all hover:scale-102 active:scale-98"
          >
            <span aria-hidden="true">🎟️</span>
            <span>Continue as Guest</span>
          </button>

        {/* Footer */}
        <p className="text-center text-xs text-white/60 mt-6 font-medium">
          BY CONTINUING, YOU AGREE TO OUR TERMS & PRIVACY POLICY
        </p>
      </motion.div>
    </div>
  )
}

export default Login