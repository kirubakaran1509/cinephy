import styles from './GenreBadge.module.css';

export default function GenreBadge({ genre }) {
  if (!genre) return null;
  return <span className={styles.badge}>{genre}</span>;
}
