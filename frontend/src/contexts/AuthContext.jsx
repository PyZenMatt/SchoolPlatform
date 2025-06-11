import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchUserProfile } from '../services/api/dashboard';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Clear wallet state from localStorage to prevent cross-user contamination
  useEffect(() => {
    localStorage.removeItem('isWalletLocked');
    localStorage.removeItem('lockedWalletAddress');
    localStorage.removeItem('connectedWalletAddress');
    console.log('🧹 Wallet localStorage cleared for per-user isolation');
  }, []);

  const refreshUser = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetchUserProfile();
      setUser(response.data);
    } catch (err) {
      console.error('Error fetching user profile:', err);
      setError('Errore nel caricamento del profilo utente');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch user if we have a token
    const token = localStorage.getItem('accessToken') || 
                  localStorage.getItem('token') || 
                  localStorage.getItem('access');
    
    if (token) {
      refreshUser();
    } else {
      setLoading(false); // Stop loading if no token
    }
  }, []);

  const value = {
    user,
    loading,
    error,
    refreshUser,
    setUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
