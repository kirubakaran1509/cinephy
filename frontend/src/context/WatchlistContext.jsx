import { createContext, useContext, useState } from 'react';
const WatchlistContext = createContext();

export function WatchlistProvider({ children }) {
  const [picks, setPicks] = useState(() => {
    try { return JSON.parse(localStorage.getItem('cinephy_picks') || '[]'); }
    catch { return []; }
  });
  const addPick = (movie) => {
    if (picks.find(p => p.id === movie.id)) return;
    const u = [...picks, movie];
    setPicks(u);
    localStorage.setItem('cinephy_picks', JSON.stringify(u));
  };
  const removePick = (id) => {
    const u = picks.filter(p => p.id !== id);
    setPicks(u);
    localStorage.setItem('cinephy_picks', JSON.stringify(u));
  };
  const clearPicks = () => {
    setPicks([]);
    localStorage.setItem('cinephy_picks', '[]');
  };
  const isPick = (id) => picks.some(p => p.id === id);
  return (
    <WatchlistContext.Provider value={{ picks, addPick, removePick, isPick, clearPicks }}>
      {children}
    </WatchlistContext.Provider>
  );
}
export const useWatchlist = () => useContext(WatchlistContext);
