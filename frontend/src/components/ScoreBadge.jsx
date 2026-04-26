import styles from './ScoreBadge.module.css';

export function scoreClass(score) {
  if (score == null || isNaN(score)) return 'mid';
  if (score >= 7.5) return 'high';
  if (score >= 6.5) return 'mid';
  return 'low';
}

export default function ScoreBadge({ score, large = false }) {
  const tier = scoreClass(score);
  const cls = `${styles.badge} ${styles[tier]} ${large ? styles.large : ''}`;
  const value = score == null || isNaN(score) ? '—' : Number(score).toFixed(1);
  return <span className={cls}>{value}</span>;
}
