import pandas as pd
import numpy as np
import pickle
import os
from collections import defaultdict

PROCESSED  = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed'
MODELS     = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\ml\saved_models'
os.makedirs(MODELS, exist_ok=True)

print('='*55)
print('STEP 3 — COLLABORATIVE FILTERING (Pure NumPy SVD)')
print('='*55)

# ── Load ratings ──────────────────────────────────────────
ratings = pd.read_csv(os.path.join(PROCESSED, 'train3_ratings_small_clean.csv'))
print(f'Ratings shape  : {ratings.shape}')
print(f'Unique users   : {ratings["userId"].nunique()}')
print(f'Unique movies  : {ratings["movieId"].nunique()}')
print(f'Rating range   : {ratings["rating"].min()} - {ratings["rating"].max()}')

# ── Encode user/movie ids to matrix indices ───────────────
user_ids  = ratings['userId'].unique()
movie_ids = ratings['movieId'].unique()

user2idx  = {u: i for i, u in enumerate(user_ids)}
movie2idx = {m: i for i, m in enumerate(movie_ids)}
idx2movie = {i: m for m, i in movie2idx.items()}

n_users  = len(user_ids)
n_movies = len(movie_ids)
print(f'Matrix size    : {n_users} x {n_movies}')

# ── Train/test split 80/20 ────────────────────────────────
np.random.seed(42)
mask      = np.random.rand(len(ratings)) < 0.8
train_df  = ratings[mask].reset_index(drop=True)
test_df   = ratings[~mask].reset_index(drop=True)
print(f'Train ratings  : {len(train_df)}')
print(f'Test ratings   : {len(test_df)}')

# ── Pure NumPy SVD (Matrix Factorization) ─────────────────
class PureSVD:
    def __init__(self, n_factors=150, n_epochs=30, lr=0.005, reg=0.02):
        self.n_factors = n_factors
        self.n_epochs  = n_epochs
        self.lr        = lr
        self.reg       = reg

    def fit(self, train_df, user2idx, movie2idx, n_users, n_movies):
        self.user2idx  = user2idx
        self.movie2idx = movie2idx
        self.global_mean = train_df['rating'].mean()

        # init latent factors + biases
        self.P  = np.random.normal(0, 0.1, (n_users,  self.n_factors))  # user factors
        self.Q  = np.random.normal(0, 0.1, (n_movies, self.n_factors))  # movie factors
        self.bu = np.zeros(n_users)   # user biases
        self.bi = np.zeros(n_movies)  # movie biases

        rows = train_df[['userId','movieId','rating']].values

        print(f'\nTraining SVD: {self.n_epochs} epochs...')
        for epoch in range(self.n_epochs):
            np.random.shuffle(rows)
            total_loss = 0
            for uid, mid, r in rows:
                u = user2idx.get(uid)
                m = movie2idx.get(mid)
                if u is None or m is None:
                    continue
                pred = (self.global_mean
                        + self.bu[u]
                        + self.bi[m]
                        + self.P[u] @ self.Q[m])
                err  = r - pred
                total_loss += err ** 2

                # update biases
                self.bu[u] += self.lr * (err - self.reg * self.bu[u])
                self.bi[m] += self.lr * (err - self.reg * self.bi[m])

                # update factors
                P_u = self.P[u].copy()
                self.P[u] += self.lr * (err * self.Q[m] - self.reg * self.P[u])
                self.Q[m] += self.lr * (err * P_u       - self.reg * self.Q[m])

            rmse = np.sqrt(total_loss / len(rows))
            if (epoch + 1) % 5 == 0:
                print(f'  Epoch {epoch+1:2d}/{self.n_epochs} — Train RMSE: {rmse:.4f}')

        return self

    def predict(self, uid, mid):
        u = self.user2idx.get(uid)
        m = self.movie2idx.get(mid)
        if u is None or m is None:
            return self.global_mean
        pred = (self.global_mean
                + self.bu[u]
                + self.bi[m]
                + self.P[u] @ self.Q[m])
        return float(np.clip(pred, 0.5, 5.0))

    def predict_for_user(self, uid, movie_ids, top_n=10):
        scores = {}
        for mid in movie_ids:
            scores[mid] = self.predict(uid, mid)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

# ── Train ─────────────────────────────────────────────────
svd = PureSVD(n_factors=150, n_epochs=30, lr=0.005, reg=0.02)
svd.fit(train_df, user2idx, movie2idx, n_users, n_movies)

# ── Evaluate on test set ──────────────────────────────────
print('\nEvaluating on test set...')
preds, actuals = [], []
for _, row in test_df.iterrows():
    p = svd.predict(row['userId'], row['movieId'])
    preds.append(p)
    actuals.append(row['rating'])

preds   = np.array(preds)
actuals = np.array(actuals)
rmse    = np.sqrt(np.mean((preds - actuals) ** 2))
mae     = np.mean(np.abs(preds - actuals))
print(f'Test RMSE : {rmse:.4f}')
print(f'Test MAE  : {mae:.4f}')

# ── Hit Rate @ 4 ──────────────────────────────────────────
print('\nComputing Hit Rate @ 4...')
all_movie_ids = ratings['movieId'].unique().tolist()

# group test by user
test_by_user  = test_df.groupby('userId')
hits, total   = 0, 0

# sample 500 users for speed
sample_users  = test_df['userId'].unique()[:500]

for uid in sample_users:
    user_test = test_by_user.get_group(uid) if uid in test_by_user.groups else None
    if user_test is None:
        continue
    relevant = set(
        user_test[user_test['rating'] >= 3.5]['movieId'].tolist()
    )
    if not relevant:
        continue
    # movies user hasn't rated in train
    train_rated  = set(train_df[train_df['userId'] == uid]['movieId'].tolist())
    candidates   = [m for m in all_movie_ids if m not in train_rated][:500]
    top4         = svd.predict_for_user(uid, candidates, top_n=4)
    recommended  = set([m for m, _ in top4])
    if recommended & relevant:
        hits += 1
    total += 1

hit_rate = hits / total if total > 0 else 0
print(f'Hit Rate @ 4 : {hit_rate:.4f}  ({hit_rate*100:.1f}%)')
print(f'Users tested : {total}')

# ── Save ──────────────────────────────────────────────────
print('\nSaving models...')
with open(os.path.join(MODELS, 'svd_model.pkl'), 'wb') as f:
    pickle.dump(svd, f)
print('Saved: svd_model.pkl')

with open(os.path.join(MODELS, 'collaborative_movie_ids.pkl'), 'wb') as f:
    pickle.dump(all_movie_ids, f)
print('Saved: collaborative_movie_ids.pkl')

with open(os.path.join(MODELS, 'user2idx.pkl'), 'wb') as f:
    pickle.dump(user2idx, f)
print('Saved: user2idx.pkl')

with open(os.path.join(MODELS, 'movie2idx.pkl'), 'wb') as f:
    pickle.dump(movie2idx, f)
print('Saved: movie2idx.pkl')

# ── File sizes ────────────────────────────────────────────
print('\nFile sizes:')
for fname in ['svd_model.pkl','collaborative_movie_ids.pkl',
              'user2idx.pkl','movie2idx.pkl']:
    fpath = os.path.join(MODELS, fname)
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        print(f'  {fname:40s} {size/1024/1024:.2f} MB')

print('\nSTEP 3 COMPLETE')
