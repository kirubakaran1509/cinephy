import { useNavigate } from 'react-router-dom';
import { Star, Bookmark, BookmarkCheck } from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext.jsx';
import GenreBadge from './GenreBadge.jsx';
import ScoreBadge from './ScoreBadge.jsx';
import styles from './MovieCard.module.css';

function primaryGenre(genres) {
  if (!genres) return '';
  if (Array.isArray(genres)) return genres[0] || '';
  return String(genres).split(',')[0].trim();
}

function genreList(genres) {
  if (!genres) return [];
  if (Array.isArray(genres)) return genres;
  return String(genres).split(',').map((g) => g.trim()).filter(Boolean);
}

export default function MovieCard({
  movie,
  showRank = false,
  compact = false,
  showGenrePills = false,
}) {
  const navigate = useNavigate();
  const { isPick, addPick, removePick } = useWatchlist();

  if (!movie) return null;

  const saved = isPick(movie.id);

  const handleClick = () => {
    if (movie.id != null) navigate(`/movie/${movie.id}`);
  };

  const handlePick = (e) => {
    e.stopPropagation();
    if (saved) removePick(movie.id);
    else addPick(movie);
  };

  const genres = genreList(movie.genres);
  const main = primaryGenre(movie.genres);

  return (
    <div
      className={`${styles.card} ${compact ? styles.compact : ''}`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') handleClick(); }}
    >
      {showRank && movie.rank != null ? (
        <div className={styles.rankBadge}>{movie.rank}</div>
      ) : null}

      <h3 className={styles.title} title={movie.title}>{movie.title}</h3>

      <div className={styles.metaRow}>
        <span>{movie.year || '—'}</span>
        {main ? <span className={styles.dot}>•</span> : null}
        {main ? <span className={styles.metaGenre}>{main}</span> : null}
      </div>

      {showGenrePills && genres.length ? (
        <div className={styles.pillRow}>
          {genres.slice(0, 3).map((g) => <GenreBadge key={g} genre={g} />)}
        </div>
      ) : null}

      {movie.vote_avg != null ? (
        <div className={styles.ratingRow}>
          <Star size={14} fill="currentColor" className={styles.star} strokeWidth={1.5} />
          <span className={styles.voteAvg}>{Number(movie.vote_avg).toFixed(1)}</span>
        </div>
      ) : null}

      {movie.director ? (
        <p className={styles.director} title={movie.director}>
          Dir. {movie.director}
        </p>
      ) : null}

      {!compact && movie.synopsis ? (
        <p className={styles.synopsis}>{movie.synopsis}</p>
      ) : null}

      <div className={styles.bottomRow}>
        <ScoreBadge score={movie.score} />
        <button
          type="button"
          className={`${styles.pickBtn} ${saved ? styles.pickBtnSaved : ''}`}
          onClick={handlePick}
        >
          {saved ? <BookmarkCheck size={14} /> : <Bookmark size={14} />}
          {saved ? 'Saved' : 'Add to Picks'}
        </button>
      </div>
    </div>
  );
}
