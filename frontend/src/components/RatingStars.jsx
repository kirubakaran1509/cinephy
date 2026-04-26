import { Star, StarHalf } from 'lucide-react';
import styles from './RatingStars.module.css';

export default function RatingStars({
  rating = 0,
  onChange,
  size = 16,
  max = 5,
}) {
  const interactive = typeof onChange === 'function';

  const stars = [];
  for (let i = 1; i <= max; i++) {
    let fill = 'empty';
    if (rating >= i) fill = 'full';
    else if (rating >= i - 0.5) fill = 'half';
    stars.push(fill);
  }

  if (interactive) {
    const halfValues = [];
    for (let i = 1; i <= max; i++) {
      halfValues.push(i - 0.5, i);
    }

    return (
      <div className={styles.wrap} role="radiogroup" aria-label="Rating">
        {stars.map((fill, idx) => (
          <span key={idx} className={styles.starWrap}>
            <button
              type="button"
              className={styles.halfBtn}
              aria-label={`Rate ${idx + 0.5}`}
              onClick={() => onChange(idx + 0.5)}
            />
            <button
              type="button"
              className={`${styles.halfBtn} ${styles.right}`}
              aria-label={`Rate ${idx + 1}`}
              onClick={() => onChange(idx + 1)}
            />
            <RenderStar fill={fill} size={size} />
          </span>
        ))}
      </div>
    );
  }

  return (
    <div className={styles.wrap}>
      {stars.map((fill, idx) => (
        <RenderStar key={idx} fill={fill} size={size} />
      ))}
    </div>
  );
}

function RenderStar({ fill, size }) {
  if (fill === 'full') {
    return (
      <Star
        size={size}
        className={styles.starFull}
        fill="currentColor"
        strokeWidth={1.5}
      />
    );
  }
  if (fill === 'half') {
    return (
      <span className={styles.halfStarBox} style={{ width: size, height: size }}>
        <Star size={size} className={styles.starEmpty} strokeWidth={1.5} />
        <StarHalf
          size={size}
          className={styles.starFull}
          fill="currentColor"
          strokeWidth={1.5}
        />
      </span>
    );
  }
  return <Star size={size} className={styles.starEmpty} strokeWidth={1.5} />;
}
