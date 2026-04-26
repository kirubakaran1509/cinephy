import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, AlertCircle, Film, Sword, Drama, Laugh, Zap, Rocket,
  Ghost, Heart, Sparkles, Skull, Compass, Wand2, HelpCircle,
} from 'lucide-react';
import Sidebar from '../components/Sidebar.jsx';
import LoadingSpinner from '../components/LoadingSpinner.jsx';
import EmptyState from '../components/EmptyState.jsx';
import GenreBadge from '../components/GenreBadge.jsx';
import ScoreBadge from '../components/ScoreBadge.jsx';
import { useWatchlist } from '../context/WatchlistContext.jsx';
import { api } from '../services/api.js';
import styles from './Discover.module.css';

const GENRE_CARDS = [
  { name: 'Action',    Icon: Sword },
  { name: 'Drama',     Icon: Drama },
  { name: 'Comedy',    Icon: Laugh },
  { name: 'Thriller',  Icon: Zap },
  { name: 'Sci-Fi',    Icon: Rocket, query: 'science fiction' },
  { name: 'Horror',    Icon: Ghost },
  { name: 'Romance',   Icon: Heart },
  { name: 'Animation', Icon: Sparkles },
  { name: 'Crime',     Icon: Skull },
  { name: 'Adventure', Icon: Compass },
  { name: 'Fantasy',   Icon: Wand2 },
  { name: 'Mystery',   Icon: HelpCircle },
];

function genreList(g) {
  if (!g) return [];
  if (Array.isArray(g)) return g;
  return String(g).split(',').map((s) => s.trim()).filter(Boolean);
}

export default function Discover() {
  const navigate = useNavigate();
  const { isPick, addPick, removePick } = useWatchlist();

  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [resultsLabel, setResultsLabel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);

  const runSearch = async (e) => {
    e?.preventDefault?.();
    if (!query.trim()) return;
    setSearched(true);
    setLoading(true);
    setError(null);
    setResults([]);
    setResultsLabel(`Results for "${query.trim()}"`);
    try {
      const res = await api.movies.search(query.trim());
      setResults(res.data?.results || []);
    } catch {
      setError('Search failed.');
    } finally {
      setLoading(false);
    }
  };

  const browseGenre = async (g) => {
    setSearched(true);
    setLoading(true);
    setError(null);
    setResults([]);
    setResultsLabel(`${g.name} movies`);
    try {
      const slug = (g.query || g.name).toLowerCase();
      const res = await api.movies.top(20, slug);
      setResults(res.data?.results || []);
    } catch {
      setError('Could not load this genre.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <header className={styles.header}>
          <h1 className={styles.title}>Discover</h1>
          <p className={styles.subtitle}>Search any movie in our database</p>
        </header>

        <form className={styles.searchBar} onSubmit={runSearch}>
          <Search size={18} className={styles.searchIcon} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search movies by title..."
            className={styles.searchInput}
          />
          <button type="submit" className={styles.searchBtn}>Search</button>
        </form>

        <section className={styles.section}>
          <h2 className={styles.sectionHeader}>Browse by Genre</h2>
          <div className={styles.genreGrid}>
            {GENRE_CARDS.map(({ name, Icon, query }) => (
              <button
                key={name}
                type="button"
                className={styles.genreCard}
                onClick={() => browseGenre({ name, query })}
              >
                <Icon size={22} className={styles.genreIcon} />
                <span className={styles.genreName}>{name}</span>
              </button>
            ))}
          </div>
        </section>

        {searched ? (
          <section className={styles.results}>
            <div className={styles.resultsHeader}>
              <h2>{resultsLabel}</h2>
              {!loading && !error ? (
                <span className={styles.count}>{results.length} found</span>
              ) : null}
            </div>

            {loading ? <LoadingSpinner /> : null}
            {!loading && error ? (
              <EmptyState icon={AlertCircle} title="Search failed" subtitle={error} />
            ) : null}
            {!loading && !error && results.length === 0 ? (
              <EmptyState icon={Film} title="No results" subtitle="Try a different keyword or genre." />
            ) : null}

            {!loading && results.length ? (
              <div className={styles.grid}>
                {results.map((m) => {
                  const saved = isPick(m.id);
                  return (
                    <article key={m.id} className={styles.card}>
                      <h3 className={styles.cardTitle}>{m.title}</h3>
                      <p className={styles.cardYear}>{m.year || '—'}</p>
                      <div className={styles.pillRow}>
                        {genreList(m.genres).slice(0, 3).map((g) => (
                          <GenreBadge key={g} genre={g} />
                        ))}
                      </div>
                      <div className={styles.cardFooter}>
                        <span className={styles.voteAvg}>
                          {m.vote_avg != null ? `★ ${Number(m.vote_avg).toFixed(1)}` : ''}
                        </span>
                        <ScoreBadge score={m.score} />
                      </div>
                      <div className={styles.actions}>
                        <button
                          type="button"
                          className={styles.btnPrimary}
                          onClick={() => navigate(`/movie/${m.id}`)}
                        >
                          More Info
                        </button>
                        <button
                          type="button"
                          className={`${styles.btnOutline} ${saved ? styles.btnSaved : ''}`}
                          onClick={() => saved ? removePick(m.id) : addPick(m)}
                        >
                          {saved ? 'Saved' : 'Add to Picks'}
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : null}
          </section>
        ) : null}
      </main>
    </div>
  );
}
