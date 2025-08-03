import { useState } from 'react';
import { auth } from '../lib/supabaseClient';

function Login() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [guestMode, setGuestMode] = useState(false);

  const signInWithGoogle = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const { error: authError } = await auth.signInWithGoogle();
      
      if (authError) {
        setError(authError.message);
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGuestMode = () => {
    setGuestMode(true);
    // Navigate to demo/guest experience
    window.location.href = '/guest';
  };

  return (
    <div className="h-full bg-gradient-to-r from-brand-blue to-brand-indigo flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-soft p-8 animate-fade-in">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold gradient-text mb-2">
              Welcome Back!
            </h1>
            <p className="text-gray-600 text-sm">
              Continue your CAPE exam preparation journey
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
              <p className="text-red-700 text-sm font-medium">
                {error}
              </p>
            </div>
          )}

          {/* Auth Buttons */}
          <div className="space-y-4">
            {/* Google OAuth Button */}
            <button
              onClick={signInWithGoogle}
              disabled={loading}
              className="w-full bg-white border-2 border-gray-200 rounded-full py-3 px-6 flex items-center justify-center space-x-3 hover:border-brand-blue hover:bg-gray-50 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover-scale"
            >
              {loading ? (
                <div className="spinner"></div>
              ) : (
                <>
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  <span className="font-medium text-gray-700">Continue with Google</span>
                </>
              )}
            </button>

            {/* TikTok Button (Disabled) */}
            <button
              disabled
              className="w-full bg-gray-100 border-2 border-gray-200 rounded-full py-3 px-6 flex items-center justify-center space-x-3 cursor-not-allowed opacity-50"
            >
              <svg className="w-5 h-5" fill="#000" viewBox="0 0 24 24">
                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.07A6.59 6.59 0 0 0 5 20.1a6.59 6.59 0 0 0 11.15-4.73v-5.21a8.23 8.23 0 0 0 4.65 1.46V7.35a4.87 4.87 0 0 1-1.21-.66z"/>
              </svg>
              <span className="font-medium text-gray-500">TikTok (Coming Soon)</span>
            </button>

            {/* Instagram Button (Disabled) */}
            <button
              disabled
              className="w-full bg-gray-100 border-2 border-gray-200 rounded-full py-3 px-6 flex items-center justify-center space-x-3 cursor-not-allowed opacity-50"
            >
              <svg className="w-5 h-5" fill="#E4405F" viewBox="0 0 24 24">
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
              </svg>
              <span className="font-medium text-gray-500">Instagram (Coming Soon)</span>
            </button>
          </div>

          {/* Divider */}
          <div className="my-8 flex items-center">
            <div className="flex-1 border-t border-gray-200"></div>
            <span className="px-4 text-sm text-gray-500 bg-white">or</span>
            <div className="flex-1 border-t border-gray-200"></div>
          </div>

          {/* Guest Mode */}
          <button
            onClick={handleGuestMode}
            disabled={guestMode}
            className="w-full bg-gray-50 hover:bg-gray-100 border-2 border-gray-200 rounded-full py-3 px-6 transition-all duration-200 hover-scale"
          >
            <span className="font-medium text-gray-700">
              {guestMode ? 'Loading guest mode...' : 'Continue as Guest'}
            </span>
          </button>

          {/* Footer */}
          <p className="text-center text-xs text-gray-500 mt-6">
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login