import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Star, Calendar, User, Users, Bookmark, BookmarkCheck,
  Clock, AlertCircle,
} from 'lucide-react';
import Sidebar from '../components/Sidebar.jsx';
import LoadingSpinner from '../components/LoadingSpinner.jsx';
import EmptyState from '../components/EmptyState.jsx';
import GenreBadge from '../components/GenreBadge.jsx';
import ScoreBadge from '../components/ScoreBadge.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useWatchlist } from '../context/WatchlistContext.jsx';
import { api } from '../services/api.js';
import styles from './MovieDetail.module.css';

function genreList(g) {
  if (!g) return [];
  if (Array.isArray(g)) return g;
  return String(g).split(',').map((s) => s.trim()).filter(Boolean);
}

function castList(c) {
  if (!c) return [];
  if (Array.isArray(c)) return c;
  return String(c).split(',').map((s) => s.trim()).filter(Boolean);
}

export default function MovieDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isPick, addPick, removePick } = useWatchlist();

  const [movie, setMovie] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [savingHistory, setSavingHistory] = useState(false);
  const [historySaved, setHistorySaved] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setMovie(null);
    setSimilar([]);
    setHistorySaved(false);

    api.movies.detail(id)
      .then((res) => {
        if (cancelled) return;
        const m = res.data?.movie || res.data;
        setMovie(m);
        if (m?.title) {
          return api.recommend.byTitle(m.title, 6).then((r) => {
            if (cancelled) return;
            setSimilar(r.data?.recommendations || []);
          }).catch(() => {});
        }
      })
      .catch(() => {
        if (cancelled) return;
        setError('Movie not found.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [id]);

  const saved = movie ? isPick(movie.id ?? id) : false;

  const handleSaveHistory = async () => {
    if (!movie || savingHistory) return;
    setSavingHistory(true);
    try {
      await api.user.saveHistory({
        user_id: String(user || 'guest'),
        movie_id: String(movie.id ?? id),
        title: movie.title,
        rating: movie.vote_avg ?? 0,
      });
      setHistorySaved(true);
    } catch {
      // ignore
    } finally {
      setSavingHistory(false);
    }
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <button type="button" className={styles.back} onClick={() => navigate(-1)}>
          <ArrowLeft size={16} /> Back
        </button>

        {loading ? <LoadingSpinner /> : null}

        {!loading && error ? (
          <EmptyState
            icon={AlertCircle}
            title="Movie not found"
            subtitle="That movie isn't in our database."
            buttonText="Back to Discover"
            buttonAction={() => navigate('/discover')}
          />
        ) : null}

        {!loading && movie ? (
          <>
            <section className={styles.hero}>
              <div className={styles.heroLeft}>
                <h1 className={styles.heroTitle}>{movie.title}</h1>
                <div className={styles.heroMeta}>
                  <span className={styles.metaChip}>
                    <Calendar size={14} /> {movie.year || '—'}
                  </span>
                  {movie.vote_avg != null ? (
                    <span className={styles.metaChip}>
                      <Star size={14} fill="currentColor" className={styles.starIcon} />
                      {Number(movie.vote_avg).toFixed(1)} / 10
                    </span>
                  ) : null}
                  <ScoreBadge score={movie.score} />
                </div>

                <div className={styles.pillRow}>
                  {genreList(movie.genres).map((g) => (
                    <GenreBadge key={g} genre={g} />
                  ))}
                </div>

                {movie.synopsis ? (
                  <p className={styles.synopsis}>{movie.synopsis}</p>
                ) : null}

                <div className={styles.heroActions}>
                  <button
                    type="button"
                    className={`${styles.btnPrimary} ${saved ? styles.btnSaved : ''}`}
                    onClick={() => saved ? removePick(movie.id ?? id) : addPick({ ...movie, id: movie.id ?? id })}
                  >
                    {saved ? (
                      <><BookmarkCheck size={16} /> In Watchlist</>
                    ) : (
                      <><Bookmark size={16} /> Add to Picks</>
                    )}
                  </button>
                  <button
                    type="button"
                    className={styles.btnOutline}
                    onClick={handleSaveHistory}
                    disabled={savingHistory}
                  >
                    <Clock size={16} />
                    {historySaved ? 'In History' : 'Save to History'}
                  </button>
                </div>
              </div>

              <aside className={styles.heroRight}>
                <h3 className={styles.asideHeader}>Details</h3>
                {movie.director ? (
                  <div className={styles.asideRow}>
                    <User size={14} className={styles.asideIcon} />
                    <div>
                      <div className={styles.asideLabel}>Director</div>
                      <div className={styles.asideValue}>{movie.director}</div>
                    </div>
                  </div>
                ) : null}
                {movie.cast ? (
                  <div className={styles.asideRow}>
                    <Users size={14} className={styles.asideIcon} />
                    <div>
                      <div className={styles.asideLabel}>Cast</div>
                      <div className={styles.asideValue}>
                        {castList(movie.cast).slice(0, 6).join(', ')}
                      </div>
                    </div>
                  </div>
                ) : null}
                {movie.runtime ? (
                  <div className={styles.asideRow}>
                    <Clock size={14} className={styles.asideIcon} />
                    <div>
                      <div className={styles.asideLabel}>Runtime</div>
                      <div className={styles.asideValue}>{movie.runtime} min</div>
                    </div>
                  </div>
                ) : null}
              </aside>
            </section>

            {similar.length ? (
              <section className={styles.similar}>
                <h2 className={styles.similarHeader}>Similar Movies</h2>
                <div className={styles.similarGrid}>
                  {similar.map((s) => (
                    <article
                      key={s.id ?? s.title}
                      className={styles.simCard}
                      role="button"
                      tabIndex={0}
                      onClick={() => navigate(`/movie/${s.id}`)}
                      onKeyDown={(e) => { if (e.key === 'Enter') navigate(`/movie/${s.id}`); }}
                    >
                      <h4 className={styles.simTitle}>{s.title}</h4>
                      <div className={styles.simMeta}>
                        <span>{s.year || '—'}</span>
                        {s.vote_avg != null ? (
                          <span className={styles.simStar}>★ {Number(s.vote_avg).toFixed(1)}</span>
                        ) : null}
                      </div>
                      <div className={styles.simPills}>
                        {genreList(s.genres).slice(0, 2).map((g) => (
                          <GenreBadge key={g} genre={g} />
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}
          </>
        ) : null}
      </main>
    </div>
  );
}
