import { Search } from 'lucide-react';
import styles from './SearchBar.module.css';

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search...',
  buttonLabel = 'Search',
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSubmit) onSubmit(value);
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <Search size={18} className={styles.icon} />
      <input
        className={styles.input}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      <button type="submit" className={styles.button}>
        {buttonLabel}
      </button>
    </form>
  );
}
