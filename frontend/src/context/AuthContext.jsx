import { createContext, useContext, useState } from 'react';
const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(
    () => localStorage.getItem('cinephy_user') || null
  );
  const login  = (u) => { localStorage.setItem('cinephy_user', u); setUser(u); };
  const logout = ()  => { localStorage.removeItem('cinephy_user'); setUser(null); };
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
export const useAuth = () => useContext(AuthContext);
