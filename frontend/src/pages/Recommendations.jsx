import { useEffect, useState } from 'react';
import { Search, AlertCircle, User, Users, Film, Clock } from 'lucide-react';
import Sidebar from '../components/Sidebar.jsx';
import LoadingSpinner from '../components/LoadingSpinner.jsx';
import EmptyState from '../components/EmptyState.jsx';
import GenreBadge from '../components/GenreBadge.jsx';
import ScoreBadge from '../components/ScoreBadge.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useWatchlist } from '../context/WatchlistContext.jsx';
import { api } from '../services/api.js';
import styles from './Recommendations.module.css';

function userIdFor(user) {
  const n = parseInt(user, 10);
  return Number.isNaN(n) ? 1 : n;
}

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

function ResultCard({ movie, showRank }) {
  const { isPick, addPick, removePick } = useWatchlist();
  const { user } = useAuth();
  const saved = isPick(movie.id);
  const [savingHist, setSavingHist] = useState(false);
  const [histDone, setHistDone] = useState(false);

  const handleSaveHistory = async () => {
    if (savingHist) return;
    setSavingHist(true);
    try {
      await api.user.saveHistory({
        user_id: String(user || 'guest'),
        movie_id: String(movie.id ?? movie.title),
        title: movie.title,
        rating: movie.vote_avg ?? 0,
      });
      setHistDone(true);
    } catch (e) {
      // ignore
    } finally {
      setSavingHist(false);
    }
  };

  return (
    <article className={styles.resCard}>
      {showRank && movie.rank != null ? (
        <div className={styles.rankBadge}>{movie.rank}</div>
      ) : null}
      <h3 className={styles.resTitle}>{movie.title}</h3>
      <div className={styles.resMeta}>
        <span>{movie.year || '—'}</span>
        <div className={styles.pillRow}>
          {genreList(movie.genres).slice(0, 3).map((g) => (
            <GenreBadge key={g} genre={g} />
          ))}
        </div>
      </div>

      {movie.director ? (
        <div className={styles.metaLine}>
          <User size={14} className={styles.metaIcon} />
          <span>{movie.director}</span>
        </div>
      ) : null}

      {movie.cast ? (
        <div className={styles.metaLine}>
          <Users size={14} className={styles.metaIcon} />
          <span className={styles.cast}>{castList(movie.cast).slice(0, 5).join(', ')}</span>
        </div>
      ) : null}

      {movie.synopsis ? (
        <p className={styles.synopsis}>{movie.synopsis}</p>
      ) : null}

      {movie.reason ? (
        <div className={styles.reason}><em>{movie.reason}</em></div>
      ) : null}

      <div className={styles.bottomRow}>
        <div className={styles.voteWrap}>
          {movie.vote_avg != null ? (
            <span className={styles.voteAvg}>★ {Number(movie.vote_avg).toFixed(1)}</span>
          ) : null}
        </div>
        <ScoreBadge score={movie.score} />
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={`${styles.btnOutlineRed} ${saved ? styles.btnSaved : ''}`}
          onClick={() => saved ? removePick(movie.id) : addPick(movie)}
        >
          {saved ? 'Saved' : 'Add to Picks'}
        </button>
        <button
          type="button"
          className={styles.btnOutline}
          onClick={handleSaveHistory}
          disabled={savingHist}
        >
          <Clock size={14} />
          {histDone ? 'In History' : 'Save to History'}
        </button>
      </div>
    </article>
  );
}

export default function Recommendations() {
  const { user } = useAuth();
  const [tab, setTab] = useState('title');

  const [title, setTitle] = useState('');
  const [n, setN] = useState(5);
  const [titleResults, setTitleResults] = useState([]);
  const [titleLoading, setTitleLoading] = useState(false);
  const [titleError, setTitleError] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const [forYou, setForYou] = useState([]);
  const [forYouLoading, setForYouLoading] = useState(false);
  const [forYouError, setForYouError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSubmitted(true);
    setTitleLoading(true);
    setTitleError(null);
    setTitleResults([]);
    try {
      const res = await api.recommend.byTitle(title.trim(), n);
      setTitleResults(res.data?.recommendations || []);
    } catch (err) {
      setTitleError(err?.response?.status === 404
        ? 'Movie not found.'
        : 'Failed to fetch recommendations.');
    } finally {
      setTitleLoading(false);
    }
  };

  useEffect(() => {
    if (tab !== 'user') return;
    let cancelled = false;
    setForYouLoading(true);
    setForYouError(null);
    api.recommend.byUser(userIdFor(user), 10)
      .then((res) => {
        if (cancelled) return;
        setForYou(res.data?.recommendations || []);
      })
      .catch(() => {
        if (cancelled) return;
        setForYouError('Could not fetch personalised recommendations.');
      })
      .finally(() => { if (!cancelled) setForYouLoading(false); });
    return () => { cancelled = true; };
  }, [tab, user]);

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <header className={styles.header}>
          <h1 className={styles.title}>Recommendations</h1>
          <p className={styles.subtitle}>Find movies you'll love by title or by your taste profile</p>
        </header>

        <div className={styles.tabs}>
          <button
            type="button"
            className={`${styles.tab} ${tab === 'title' ? styles.tabActive : ''}`}
            onClick={() => setTab('title')}
          >By Movie Title</button>
          <button
            type="button"
            className={`${styles.tab} ${tab === 'user' ? styles.tabActive : ''}`}
            onClick={() => setTab('user')}
          >For You</button>
        </div>

        {tab === 'title' ? (
          <>
            <form className={styles.searchPanel} onSubmit={handleSearch}>
              <div className={styles.searchInputWrap}>
                <Search size={18} className={styles.searchIcon} />
                <input
                  type="text"
                  className={styles.searchInput}
                  placeholder="Enter a movie title..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div className={styles.numWrap}>
                <label className={styles.numLabel}>Results</label>
                <select
                  className={styles.select}
                  value={n}
                  onChange={(e) => setN(parseInt(e.target.value, 10))}
                >
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                </select>
              </div>
              <button type="submit" className={styles.submitBtn}>
                Get Recommendations
              </button>
            </form>

            {titleLoading ? <LoadingSpinner /> : null}

            {!titleLoading && titleError ? (
              <EmptyState
                icon={AlertCircle}
                title="Movie not found"
                subtitle={titleError}
              />
            ) : null}

            {!titleLoading && !titleError && submitted && titleResults.length === 0 ? (
              <EmptyState icon={Film} title="No matches" subtitle="Try another title." />
            ) : null}

            {!titleLoading && titleResults.length ? (
              <div className={styles.grid}>
                {titleResults.map((m) => (
                  <ResultCard key={m.id ?? m.rank ?? m.title} movie={m} showRank />
                ))}
              </div>
            ) : null}
          </>
        ) : (
          <>
            {forYouLoading ? <LoadingSpinner /> : null}
            {!forYouLoading && forYouError ? (
              <EmptyState
                icon={AlertCircle}
                title="Could not load"
                subtitle={forYouError}
              />
            ) : null}
            {!forYouLoading && !forYouError && forYou.length === 0 ? (
              <EmptyState
                icon={Film}
                title="No personalised recommendations yet"
                subtitle="Rate or watch a few titles to train your profile."
              />
            ) : null}
            {!forYouLoading && forYou.length ? (
              <div className={styles.grid}>
                {forYou.map((m) => (
                  <ResultCard key={m.id ?? m.title} movie={m} />
                ))}
              </div>
            ) : null}
          </>
        )}
      </main>
    </div>
  );
}
