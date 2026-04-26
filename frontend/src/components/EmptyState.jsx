import styles from './EmptyState.module.css';

export default function EmptyState({
  icon: Icon,
  title,
  subtitle,
  buttonText,
  buttonAction,
}) {
  return (
    <div className={styles.wrap}>
      {Icon ? (
        <div className={styles.iconWrap}>
          <Icon size={48} />
        </div>
      ) : null}
      {title ? <h3 className={styles.title}>{title}</h3> : null}
      {subtitle ? <p className={styles.subtitle}>{subtitle}</p> : null}
      {buttonText && buttonAction ? (
        <button type="button" className={styles.button} onClick={buttonAction}>
          {buttonText}
        </button>
      ) : null}
    </div>
  );
}
