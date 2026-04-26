import { useNavigate } from 'react-router-dom';
import { Bookmark, Trash2, Star } from 'lucide-react';
import Sidebar from '../components/Sidebar.jsx';
import EmptyState from '../components/EmptyState.jsx';
import GenreBadge from '../components/GenreBadge.jsx';
import ScoreBadge from '../components/ScoreBadge.jsx';
import RatingStars from '../components/RatingStars.jsx';
import { useWatchlist } from '../context/WatchlistContext.jsx';
import styles from './MyPicks.module.css';

function genreList(g) {
  if (!g) return [];
  if (Array.isArray(g)) return g;
  return String(g).split(',').map((s) => s.trim()).filter(Boolean);
}

export default function MyPicks() {
  const { picks, removePick } = useWatchlist();
  const navigate = useNavigate();

  const total = picks.length;
  const avgScore = total
    ? (picks.reduce((s, m) => s + (Number(m.score) || 0), 0) / total).toFixed(1)
    : '—';

  const genreCounts = {};
  picks.forEach((m) => {
    genreList(m.genres).forEach((g) => {
      genreCounts[g] = (genreCounts[g] || 0) + 1;
    });
  });
  const topGenre = Object.entries(genreCounts)
    .sort((a, b) => b[1] - a[1])[0]?.[0] || '—';

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <header className={styles.header}>
          <h1 className={styles.title}>My Picks</h1>
          <p className={styles.subtitle}>Your personal watchlist</p>
        </header>

        <div className={styles.stats}>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Total Picks</span>
            <span className={styles.statValue}>{total}</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Average Score</span>
            <span className={styles.statValue}>{avgScore}</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Top Genre</span>
            <span className={styles.statValue}>{topGenre}</span>
          </div>
        </div>

        {total === 0 ? (
          <EmptyState
            icon={Bookmark}
            title="Your watchlist is empty"
            subtitle="Browse movies and add them to your picks"
            buttonText="Discover Movies"
            buttonAction={() => navigate('/discover')}
          />
        ) : (
          <div className={styles.grid}>
            {picks.map((m) => (
              <article key={m.id} className={styles.card}>
                <h3 className={styles.cardTitle}>{m.title}</h3>
                <div className={styles.metaRow}>
                  <span>{m.year || '—'}</span>
                  <div className={styles.pillRow}>
                    {genreList(m.genres).slice(0, 2).map((g) => (
                      <GenreBadge key={g} genre={g} />
                    ))}
                  </div>
                </div>
                {m.director ? (
                  <p className={styles.director}>Dir. {m.director}</p>
                ) : null}
                <div className={styles.scoreRow}>
                  <ScoreBadge score={m.score} />
                  {m.vote_avg != null ? (
                    <span className={styles.voteAvg}>
                      <Star size={13} fill="currentColor" /> {Number(m.vote_avg).toFixed(1)}
                    </span>
                  ) : null}
                </div>
                {m.synopsis ? (
                  <p className={styles.synopsis}>{m.synopsis}</p>
                ) : null}
                <div className={styles.bottomRow}>
                  <RatingStars rating={Math.min(5, (Number(m.vote_avg) || 0) / 2)} />
                  <div className={styles.btnRow}>
                    <button
                      type="button"
                      className={styles.infoBtn}
                      onClick={() => navigate(`/movie/${m.id}`)}
                    >
                      More Info
                    </button>
                    <button
                      type="button"
                      className={styles.removeBtn}
                      onClick={() => removePick(m.id)}
                      aria-label="Remove from picks"
                    >
                      <Trash2 size={14} /> Remove
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
