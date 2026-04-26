import { useEffect, useState } from 'react';
import { History as HistoryIcon, AlertCircle, Star } from 'lucide-react';
import Sidebar from '../components/Sidebar.jsx';
import LoadingSpinner from '../components/LoadingSpinner.jsx';
import EmptyState from '../components/EmptyState.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { api } from '../services/api.js';
import styles from './History.module.css';

function formatDate(d) {
  if (!d) return '';
  try {
    return new Date(d).toLocaleString();
  } catch {
    return String(d);
  }
}

export default function History() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.user.getHistory(String(user || 'guest'))
      .then((res) => {
        if (cancelled) return;
        const list = res.data?.history || res.data?.results || res.data || [];
        setItems(Array.isArray(list) ? list : []);
      })
      .catch(() => {
        if (cancelled) return;
        setError('Could not load history.');
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [user]);

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <header className={styles.header}>
          <h1 className={styles.title}>History</h1>
          <p className={styles.subtitle}>Movies you've rated and watched</p>
        </header>

        {loading ? <LoadingSpinner /> : null}

        {!loading && error ? (
          <EmptyState icon={AlertCircle} title="Could not load" subtitle={error} />
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <EmptyState
            icon={HistoryIcon}
            title="No history yet"
            subtitle="Save a movie from any recommendation to see it here."
          />
        ) : null}

        {!loading && items.length ? (
          <div className={styles.list}>
            {items.map((row, i) => (
              <div key={`${row.movie_id ?? row.title}-${i}`} className={styles.row}>
                <div className={styles.rowMain}>
                  <h3 className={styles.rowTitle}>{row.title || row.movie_title || `Movie ${row.movie_id}`}</h3>
                  <span className={styles.timestamp}>{formatDate(row.timestamp || row.watched_at || row.created_at)}</span>
                </div>
                <div className={styles.rating}>
                  <Star size={14} className={styles.star} fill="currentColor" />
                  <span>{row.rating != null ? Number(row.rating).toFixed(1) : '—'}</span>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </main>
    </div>
  );
}
