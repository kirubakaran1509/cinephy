import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext.jsx';
import { WatchlistProvider } from './context/WatchlistContext.jsx';
import Login from './pages/Login.jsx';
import Home from './pages/Home.jsx';
import Recommendations from './pages/Recommendations.jsx';
import Trending from './pages/Trending.jsx';
import Discover from './pages/Discover.jsx';
import MyPicks from './pages/MyPicks.jsx';
import History from './pages/History.jsx';
import MovieDetail from './pages/MovieDetail.jsx';
import Settings from './pages/Settings.jsx';

function Guard({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

const basename = (import.meta.env.BASE_URL || '/').replace(/\/$/, '');

export default function App() {
  return (
    <AuthProvider>
      <WatchlistProvider>
        <BrowserRouter basename={basename}>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/home" element={<Guard><Home /></Guard>} />
            <Route path="/recommendations" element={<Guard><Recommendations /></Guard>} />
            <Route path="/trending" element={<Guard><Trending /></Guard>} />
            <Route path="/discover" element={<Guard><Discover /></Guard>} />
            <Route path="/mypicks" element={<Guard><MyPicks /></Guard>} />
            <Route path="/history" element={<Guard><History /></Guard>} />
            <Route path="/movie/:id" element={<Guard><MovieDetail /></Guard>} />
            <Route path="/settings" element={<Guard><Settings /></Guard>} />
          </Routes>
        </BrowserRouter>
      </WatchlistProvider>
    </AuthProvider>
  );
}
