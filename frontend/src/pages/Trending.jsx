import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ThumbsUp, AlertCircle, Film } from 'lucide-react';
import Sidebar from '../components/Sidebar.jsx';
import LoadingSpinner from '../components/LoadingSpinner.jsx';
import EmptyState from '../components/EmptyState.jsx';
import GenreBadge from '../components/GenreBadge.jsx';
import ScoreBadge from '../components/ScoreBadge.jsx';
import { useWatchlist } from '../context/WatchlistContext.jsx';
import { api } from '../services/api.js';
import styles from './Trending.module.css';

const GENRES = [
  'All', 'Action', 'Drama', 'Comedy', 'Thriller', 'Science Fiction',
  'Horror', 'Romance', 'Animation', 'Crime', 'Adventure',
];

function genreList(g) {
  if (!g) return [];
  if (Array.isArray(g)) return g;
  return String(g).split(',').map((s) => s.trim()).filter(Boolean);
}

export default function Trending() {
  const navigate = useNavigate();
  const { isPick, addPick, removePick } = useWatchlist();

  const [active, setActive] = useState('All');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const call = active === 'All'
      ? api.movies.top(20)
      : api.movies.top(20, active.toLowerCase());
    call.then((res) => {
      if (cancelled) return;
      setResults(res.data?.results || []);
    }).catch(() => {
      if (cancelled) return;
      setError('Could not load trending movies.');
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [active]);

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <header className={styles.header}>
          <h1 className={styles.title}>Trending Now</h1>
          <p className={styles.subtitle}>Top rated movies across all genres</p>
        </header>

        <div className={styles.pillRow}>
          {GENRES.map((g) => (
            <button
              key={g}
              type="button"
              className={`${styles.pill} ${active === g ? styles.pillActive : ''}`}
              onClick={() => setActive(g)}
            >
              {g}
            </button>
          ))}
        </div>

        {loading ? <LoadingSpinner /> : null}
        {!loading && error ? (
          <EmptyState icon={AlertCircle} title="Could not load" subtitle={error} />
        ) : null}
        {!loading && !error && results.length === 0 ? (
          <EmptyState icon={Film} title="No movies" subtitle="No movies in this category." />
        ) : null}

        {!loading && results.length ? (
          <div className={styles.grid}>
            {results.map((m, idx) => {
              const saved = isPick(m.id);
              const genres = genreList(m.genres);
              return (
                <article
                  key={m.id ?? idx}
                  className={styles.card}
                  onClick={() => navigate(`/movie/${m.id}`)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === 'Enter') navigate(`/movie/${m.id}`); }}
                >
                  <div className={styles.rankFaded}>{(idx + 1).toString().padStart(2, '0')}</div>
                  <div className={styles.cardBody}>
                    <h3 className={styles.cardTitle}>{m.title}</h3>
                    <p className={styles.cardYear}>{m.year || '—'}</p>
                    <div className={styles.cardPills}>
                      {genres.slice(0, 2).map((g) => <GenreBadge key={g} genre={g} />)}
                    </div>
                    {m.director ? (
                      <p className={styles.cardDirector}>Dir. {m.director}</p>
                    ) : null}
                    {m.synopsis ? (
                      <p className={styles.cardSynopsis}>{m.synopsis}</p>
                    ) : null}
                    <div className={styles.cardFooter}>
                      <span className={styles.voteRow}>
                        {m.vote_avg != null ? (
                          <>
                            <ThumbsUp size={13} />
                            <span>{Number(m.vote_avg).toFixed(1)}</span>
                          </>
                        ) : null}
                      </span>
                      <ScoreBadge score={m.score} />
                    </div>
                    <button
                      type="button"
                      className={`${styles.pickBtn} ${saved ? styles.pickBtnSaved : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (saved) removePick(m.id); else addPick(m);
                      }}
                    >
                      {saved ? 'Saved' : 'Add to Picks'}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : null}
      </main>
    </div>
  );
}
