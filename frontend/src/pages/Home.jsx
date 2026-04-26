import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Star, AlertCircle, Bookmark, BookmarkCheck } from 'lucide-react';
import Sidebar from '../components/Sidebar.jsx';
import MovieCard from '../components/MovieCard.jsx';
import LoadingSpinner from '../components/LoadingSpinner.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useWatchlist } from '../context/WatchlistContext.jsx';
import { api } from '../services/api.js';
import styles from './Home.module.css';

function userIdFor(user) {
  const n = parseInt(user, 10);
  return Number.isNaN(n) ? 1 : n;
}

function genresStr(g) {
  if (!g) return '';
  if (Array.isArray(g)) return g.join(', ');
  return String(g);
}

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { isPick, addPick, removePick } = useWatchlist();

  const [hero, setHero] = useState(null);
  const [recs, setRecs] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.allSettled([
      api.movies.top(1),
      api.recommend.byUser(userIdFor(user), 5),
      api.movies.top(10),
    ]).then((results) => {
      if (cancelled) return;
      const [heroRes, recsRes, trendRes] = results;
      const allFailed = results.every((r) => r.status === 'rejected');
      if (allFailed) {
        setError('Could not reach the recommendation service. Make sure the Flask backend is running on http://localhost:5000.');
        setLoading(false);
        return;
      }
      if (heroRes.status === 'fulfilled') {
        setHero(heroRes.value.data?.results?.[0] || null);
      }
      if (recsRes.status === 'fulfilled') {
        setRecs(recsRes.value.data?.recommendations || []);
      }
      if (trendRes.status === 'fulfilled') {
        setTrending(trendRes.value.data?.results || []);
      }
      setLoading(false);
    });

    return () => { cancelled = true; };
  }, [user]);

  const heroSaved = hero && isPick(hero.id);

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className={styles.errorCard}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        ) : (
          <>
            {hero ? (
              <section className={styles.hero}>
                <div className={styles.heroLeft}>
                  <span className={styles.featuredPill}>FEATURED</span>
                  <h1 className={styles.heroTitle}>{hero.title}</h1>
                  <div className={styles.heroMeta}>
                    <Star size={16} fill="currentColor" className={styles.heroStar} strokeWidth={1.5} />
                    <span className={styles.heroScore}>
                      {hero.vote_avg != null ? Number(hero.vote_avg).toFixed(1) : '—'}
                    </span>
                    <span className={styles.dot}>•</span>
                    <span>{hero.year || '—'}</span>
                    {genresStr(hero.genres) ? <><span className={styles.dot}>•</span><span>{genresStr(hero.genres)}</span></> : null}
                  </div>
                  {hero.synopsis ? (
                    <p className={styles.heroSyn}>{hero.synopsis}</p>
                  ) : null}
                  <div className={styles.heroActions}>
                    <button
                      className={styles.btnPrimary}
                      onClick={() => navigate(`/movie/${hero.id}`)}
                    >
                      More Info
                    </button>
                    <button
                      className={styles.btnOutline}
                      onClick={() => heroSaved ? removePick(hero.id) : addPick(hero)}
                    >
                      {heroSaved ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}
                      {heroSaved ? 'In Watchlist' : 'Add to Watchlist'}
                    </button>
                  </div>
                </div>
                <div className={styles.heroRight}>
                  <span className={styles.watermark}>{hero.title}</span>
                </div>
              </section>
            ) : null}

            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Recommended For You</h2>
                <Link className={styles.viewAll} to="/recommendations">View All</Link>
              </div>
              {recs.length ? (
                <div className={styles.row}>
                  {recs.slice(0, 5).map((m) => (
                    <MovieCard key={m.id ?? m.rank ?? m.title} movie={m} showRank />
                  ))}
                </div>
              ) : (
                <p className={styles.emptyText}>No personalised picks yet.</p>
              )}
            </section>

            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Trending Now</h2>
                <Link className={styles.viewAll} to="/trending">View All</Link>
              </div>
              {trending.length ? (
                <div className={styles.row}>
                  {trending.slice(0, 5).map((m) => (
                    <MovieCard key={m.id ?? m.title} movie={m} compact />
                  ))}
                </div>
              ) : (
                <p className={styles.emptyText}>No trending data available.</p>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
