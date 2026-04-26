import { NavLink, useNavigate } from 'react-router-dom';
import {
  Film, Home, Star, TrendingUp, Search, Bookmark, Clock, Settings, LogOut
} from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import styles from './Sidebar.module.css';

const links = [
  { to: '/home',            label: 'Home',            Icon: Home },
  { to: '/recommendations', label: 'Recommendations', Icon: Star },
  { to: '/trending',        label: 'Trending',        Icon: TrendingUp },
  { to: '/discover',        label: 'Discover',        Icon: Search },
  { to: '/mypicks',         label: 'My Picks',        Icon: Bookmark },
  { to: '/history',         label: 'History',         Icon: Clock },
  { to: '/settings',        label: 'Settings',        Icon: Settings },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const initial = (user || 'G').trim().charAt(0).toUpperCase();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <Film size={22} className={styles.brandIcon} />
        <span className={styles.brandText}>Cinephy</span>
      </div>

      <nav className={styles.nav}>
        {links.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.linkActive : ''}`
            }
          >
            <Icon size={18} className={styles.linkIcon} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.userBar}>
        <div className={styles.avatar}>{initial}</div>
        <div className={styles.username} title={user || 'guest'}>
          {user || 'guest'}
        </div>
        <button
          type="button"
          className={styles.logoutBtn}
          onClick={handleLogout}
          aria-label="Log out"
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
}
