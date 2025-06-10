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
    // Only fetch user if we might be authenticated
    // You can add logic here to check if there's a token
    refreshUser();
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
