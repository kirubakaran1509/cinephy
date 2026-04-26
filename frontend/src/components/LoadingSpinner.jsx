import styles from './LoadingSpinner.module.css';

export default function LoadingSpinner({ label = 'Loading...' }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.spinner} />
      <p className={styles.label}>{label}</p>
    </div>
  );
}
