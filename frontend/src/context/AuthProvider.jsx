import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';
import { useNavigate, useLocation } from 'react-router-dom';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [session, setSession] = useState(null);  // null | 'guest' | SupabaseSession
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  // Initial session fetch
  useEffect(() => {
    const bootstrap = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        const guest = localStorage.getItem('cape_session') === 'guest';
        setSession(session ?? (guest ? 'guest' : null));
      } catch (error) {
        console.error('Error getting session:', error);
        // Check for guest session even if Supabase fails
        const guest = localStorage.getItem('cape_session') === 'guest';
        setSession(guest ? 'guest' : null);
      } finally {
        setLoading(false);
      }
    };
    
    bootstrap();
  }, []);

  // Live auth state listener
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, sess) => {
        console.log('Auth state change:', event, sess);
        if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
          setSession(sess);
        }
        if (event === 'SIGNED_OUT') {
          setSession(null);
          localStorage.removeItem('cape_session');
        }
        setLoading(false);
      }
    );
    
    return () => subscription.unsubscribe();
  }, []);

  // Auto-redirect once authenticated
  useEffect(() => {
    if (!loading && session && location.pathname === '/login') {
      navigate('/', { replace: true });
    }
  }, [loading, session, location.pathname, navigate]);

  // Helpers
  const loginGuest = () => {
    localStorage.setItem('cape_session', 'guest');
    setSession('guest');
    navigate('/', { replace: true });
  };

  const logout = async () => {
    localStorage.removeItem('cape_session');
    await supabase.auth.signOut();
    setSession(null);
    navigate('/login', { replace: true });
  };

  const signInWithGoogle = async () => {
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/`
        }
      });
      
      if (error) {
        console.error('Google sign in error:', error);
        throw error;
      }
      
      return data;
    } catch (error) {
      console.error('Error signing in with Google:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ 
      session, 
      loading, 
      loginGuest, 
      logout, 
      signInWithGoogle 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};