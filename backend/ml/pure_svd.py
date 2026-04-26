import numpy as np

class PureSVD:
    def __init__(self, n_factors=100, n_epochs=20, lr=0.005, reg=0.02):
        self.n_factors   = n_factors
        self.n_epochs    = n_epochs
        self.lr          = lr
        self.reg         = reg
        self.user2idx    = {}
        self.movie2idx   = {}
        self.global_mean = 0.0
        self.P  = None
        self.Q  = None
        self.bu = None
        self.bi = None

    def fit(self, train_df, user2idx, movie2idx, n_users, n_movies):
        self.user2idx    = user2idx
        self.movie2idx   = movie2idx
        self.global_mean = float(train_df['rating'].mean())
        self.P  = np.random.normal(0, 0.1, (n_users,  self.n_factors))
        self.Q  = np.random.normal(0, 0.1, (n_movies, self.n_factors))
        self.bu = np.zeros(n_users)
        self.bi = np.zeros(n_movies)
        rows = train_df[['userId','movieId','rating']].values.tolist()
        for epoch in range(self.n_epochs):
            import random; random.shuffle(rows)
            loss = 0
            for uid, mid, r in rows:
                u = self.user2idx.get(uid)
                m = self.movie2idx.get(mid)
                if u is None or m is None: continue
                pred = self.global_mean + self.bu[u] + self.bi[m] + self.P[u] @ self.Q[m]
                err  = r - pred
                loss += err**2
                self.bu[u] += self.lr * (err - self.reg * self.bu[u])
                self.bi[m] += self.lr * (err - self.reg * self.bi[m])
                Pu = self.P[u].copy()
                self.P[u] += self.lr * (err * self.Q[m] - self.reg * self.P[u])
                self.Q[m] += self.lr * (err * Pu        - self.reg * self.Q[m])
            rmse = np.sqrt(loss / len(rows))
            if (epoch+1) % 5 == 0:
                print(f'  Epoch {epoch+1}/{self.n_epochs}  Train RMSE: {rmse:.4f}')
        return self

    def predict(self, uid, mid):
        u = self.user2idx.get(uid)
        m = self.movie2idx.get(mid)
        if u is None or m is None: return self.global_mean
        pred = self.global_mean + self.bu[u] + self.bi[m] + self.P[u] @ self.Q[m]
        return float(np.clip(pred, 0.5, 5.0))

    def predict_for_user(self, uid, movie_ids, top_n=10):
        scores = {mid: self.predict(uid, mid) for mid in movie_ids}
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
