import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Film, User, Lock, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import styles from './Login.module.css';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);

  const handleSignIn = (e) => {
    e.preventDefault();
    const value = username.trim() || 'guest';
    login(value);
    navigate('/home', { replace: true });
  };

  const handleGuest = () => {
    login('guest');
    navigate('/home', { replace: true });
  };

  return (
    <div className={styles.shell}>
      <div className={styles.left}>
        <div className={styles.logo}>
          <Film size={36} className={styles.logoIcon} />
          <span className={styles.logoText}>Cinephy</span>
        </div>
        <h2 className={styles.tagline}>Discover Movies, Powered by AI</h2>
        <p className={styles.lead}>
          Personal recommendations driven by a hybrid of content similarity,
          collaborative filtering and quality scoring across a 73 million rating
          dataset.
        </p>
      </div>

      <div className={styles.right}>
        <form className={styles.card} onSubmit={handleSignIn}>
          <h1 className={styles.title}>Welcome Back</h1>
          <p className={styles.subtitle}>Sign in to your account</p>

          <label className={styles.label}>Username</label>
          <div className={styles.inputWrap}>
            <User size={16} className={styles.inputIcon} />
            <input
              type="text"
              className={styles.input}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              autoComplete="username"
            />
          </div>

          <label className={styles.label}>Password</label>
          <div className={styles.inputWrap}>
            <Lock size={16} className={styles.inputIcon} />
            <input
              type={showPw ? 'text' : 'password'}
              className={styles.input}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
            />
            <button
              type="button"
              className={styles.toggle}
              onClick={() => setShowPw((v) => !v)}
              aria-label={showPw ? 'Hide password' : 'Show password'}
            >
              {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          <button type="submit" className={styles.primary}>Sign In</button>

          <div className={styles.divider}><span>or</span></div>

          <button
            type="button"
            className={styles.outline}
            onClick={handleGuest}
          >
            Continue as Guest
          </button>
        </form>
      </div>
    </div>
  );
}
