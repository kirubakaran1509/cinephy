import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Trash2, User as UserIcon, Database } from 'lucide-react';
import Sidebar from '../components/Sidebar.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useWatchlist } from '../context/WatchlistContext.jsx';
import styles from './Settings.module.css';

export default function Settings() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { picks, clearPicks } = useWatchlist();
  const [confirming, setConfirming] = useState(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleClearPicks = () => {
    clearPicks();
    setConfirming(null);
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <header className={styles.header}>
          <h1 className={styles.title}>Settings</h1>
          <p className={styles.subtitle}>Manage your account and data</p>
        </header>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <UserIcon size={18} />
            <h2>Profile</h2>
          </div>
          <div className={styles.cardBody}>
            <div className={styles.row}>
              <span className={styles.label}>Username</span>
              <span className={styles.value}>{user || 'Guest'}</span>
            </div>
          </div>
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <Database size={18} />
            <h2>Data</h2>
          </div>
          <div className={styles.cardBody}>
            <div className={styles.row}>
              <div>
                <div className={styles.label}>My Picks</div>
                <div className={styles.muted}>{picks.length} saved movie{picks.length === 1 ? '' : 's'}</div>
              </div>
              {confirming === 'picks' ? (
                <div className={styles.confirmRow}>
                  <span className={styles.confirmText}>Are you sure?</span>
                  <button type="button" className={styles.btnDanger} onClick={handleClearPicks}>
                    Yes, clear
                  </button>
                  <button type="button" className={styles.btnGhost} onClick={() => setConfirming(null)}>
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  className={styles.btnDangerOutline}
                  disabled={picks.length === 0}
                  onClick={() => setConfirming('picks')}
                >
                  <Trash2 size={14} /> Clear All Picks
                </button>
              )}
            </div>
          </div>
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <LogOut size={18} />
            <h2>Session</h2>
          </div>
          <div className={styles.cardBody}>
            <div className={styles.row}>
              <span className={styles.muted}>Sign out of your account</span>
              <button type="button" className={styles.btnDanger} onClick={handleLogout}>
                <LogOut size={14} /> Sign Out
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
