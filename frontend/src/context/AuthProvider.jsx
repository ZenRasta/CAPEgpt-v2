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
      console.log('AuthProvider: Starting bootstrap...');
      
      try {
        // Set a timeout for Supabase request
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Supabase timeout')), 3000)
        );
        
        const supabasePromise = supabase.auth.getSession();
        
        const { data: { session } } = await Promise.race([supabasePromise, timeoutPromise]);
        console.log('AuthProvider: Supabase session:', session);
        
        const guest = localStorage.getItem('cape_session') === 'guest';
        console.log('AuthProvider: Guest session:', guest);
        
        setSession(session ?? (guest ? 'guest' : null));
      } catch (error) {
        console.error('AuthProvider: Error getting session:', error);
        // Always check for guest session if Supabase fails
        const guest = localStorage.getItem('cape_session') === 'guest';
        console.log('AuthProvider: Fallback to guest session:', guest);
        setSession(guest ? 'guest' : null);
      } finally {
        console.log('AuthProvider: Bootstrap complete, setting loading to false');
        setLoading(false);
      }
    };
    
    bootstrap();
  }, []);

  // Live auth state listener
  useEffect(() => {
    let subscription;
    
    try {
      const { data: { subscription: sub } } = supabase.auth.onAuthStateChange(
        (event, sess) => {
          console.log('AuthProvider: Auth state change:', event, sess);
          if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
            setSession(sess);
            setLoading(false);
          }
          if (event === 'SIGNED_OUT') {
            setSession(null);
            localStorage.removeItem('cape_session');
            setLoading(false);
          }
        }
      );
      subscription = sub;
    } catch (error) {
      console.error('AuthProvider: Error setting up auth listener:', error);
      // Continue without auth listener - app will still work with guest mode
    }
    
    return () => {
      if (subscription) {
        subscription.unsubscribe();
      }
    };
  }, []);

  // Auto-redirect once authenticated (for OAuth flow)
  useEffect(() => {
    console.log('Auto-redirect check:', { loading, session, pathname: location.pathname });
    if (!loading && session && session !== 'guest' && location.pathname === '/login') {
      console.log('Auto-redirecting to home after OAuth...');
      navigate('/', { replace: true });
    }
  }, [loading, session, location.pathname, navigate]);

  // Helpers
  const loginGuest = () => {
    console.log('Guest login clicked');
    localStorage.setItem('cape_session', 'guest');
    setSession('guest');
    setLoading(false); // Ensure loading is false for guest
    console.log('Navigating to home...');
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