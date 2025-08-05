import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthProvider';
import { Navigate } from 'react-router-dom';
import { GlassCard, GlassButton } from '../components/GlassCard';

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
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-hyper-violet/20 via-bubblegum-pink/20 to-electric-cyan/20 blur-3xl" />
      <div className="absolute top-20 left-20 w-96 h-96 bg-lime-slush/10 rounded-full blur-2xl" />
      <div className="absolute bottom-20 right-20 w-72 h-72 bg-electric-cyan/10 rounded-full blur-2xl" />
      
      <motion.div 
        className="w-full max-w-md relative z-10"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <GlassCard className="p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <motion.h1 
              className="text-4xl font-extrabold gen-gradient-text mb-4 tracking-tight"
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
              className="mb-6 p-4 gen-glass-card bg-red-500/20 border border-red-400/30"
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
              className="w-full gen-glass-card p-4 flex items-center justify-center gap-3 hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {loading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-6 h-6 border-2 border-electric-cyan border-t-transparent rounded-full"
                />
              ) : (
                <>
                  <svg className="w-6 h-6" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  <span className="font-bold text-white tracking-wide">CONTINUE WITH GOOGLE</span>
                </>
              )}
            </motion.button>

            {/* TikTok Button (Disabled) */}
            <button
              disabled
              className="w-full gen-glass-card p-4 flex items-center justify-center gap-3 opacity-50 cursor-not-allowed"
            >
              <svg className="w-6 h-6" fill="#000" viewBox="0 0 24 24">
                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.07A6.59 6.59 0 0 0 5 20.1a6.59 6.59 0 0 0 11.15-4.73v-5.21a8.23 8.23 0 0 0 4.65 1.46V7.35a4.87 4.87 0 0 1-1.21-.66z"/>
              </svg>
              <span className="font-bold text-white/50 tracking-wide">TIKTOK (COMING SOON)</span>
            </button>

            {/* Instagram Button (Disabled) */}
            <button
              disabled
              className="w-full gen-glass-card p-4 flex items-center justify-center gap-3 opacity-50 cursor-not-allowed"
            >
              <svg className="w-6 h-6" fill="#E4405F" viewBox="0 0 24 24">
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
              </svg>
              <span className="font-bold text-white/50 tracking-wide">INSTAGRAM (COMING SOON)</span>
            </button>
          </div>

          {/* Divider */}
          <div className="my-8 flex items-center">
            <div className="flex-1 border-t border-white/20"></div>
            <span className="px-4 text-sm text-white/60 font-medium tracking-wide">OR</span>
            <div className="flex-1 border-t border-white/20"></div>
          </div>

          {/* Guest Mode */}
          <GlassButton 
            variant="secondary" 
            onClick={handleGuestMode}
            className="w-full py-4 text-lg font-bold tracking-wide"
          >
            CONTINUE AS GUEST 👤
          </GlassButton>

          {/* Footer */}
          <p className="text-center text-xs text-white/60 mt-6 font-medium">
            BY CONTINUING, YOU AGREE TO OUR TERMS & PRIVACY POLICY
          </p>
        </GlassCard>
      </motion.div>
    </div>
  )
}

export default Login