import warnings
warnings.filterwarnings("ignore")
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import pandas as pd
import numpy as np
import pickle
from ml.pure_svd import PureSVD, WeightedEnsemble
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.base import BaseEstimator, RegressorMixin
import xgboost as xgb

PROCESSED    = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed'
SAVED_MODELS = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\ml\saved_models'

feature_cols = ['budget','revenue','runtime','popularity',
                'rating_count','rating_std','avg_rating',
                'genre_encoded','language_encoded','year']

class WeightedEnsemble(BaseEstimator, RegressorMixin):
    def __init__(self, rf, xgb, gbr, weights=(0.40, 0.35, 0.25)):
        self.rf      = rf
        self.xgb     = xgb
        self.gbr     = gbr
        self.weights = weights
        self.feature_cols = None
    def fit(self, X, y): return self
    def predict(self, X):
        if not isinstance(X, pd.DataFrame):
            cols = self.feature_cols if self.feature_cols else feature_cols
            X = pd.DataFrame(X, columns=cols)
        return (self.weights[0] * self.rf.predict(X)  +
                self.weights[1] * self.xgb.predict(X) +
                self.weights[2] * self.gbr.predict(X))

df = pd.read_csv(os.path.join(PROCESSED, 'master_movies.csv'))
df['id_str']  = df['id'].astype(str)
master_lookup = df.set_index('id_str')
master_lookup = master_lookup[~master_lookup.index.duplicated(keep='first')]

with open(os.path.join(SAVED_MODELS,'svd_model.pkl'),      'rb') as f: svd      = pickle.load(f)
with open(os.path.join(SAVED_MODELS,'ensemble_model.pkl'), 'rb') as f: ensemble = pickle.load(f)

ratings = pd.read_csv(os.path.join(PROCESSED,'train3_ratings_small_clean.csv'))
np.random.seed(42)
mask    = np.random.rand(len(ratings)) < 0.8
train_r = ratings[mask]
test_r  = ratings[~mask]

def get_content_score(mid):
    mid_str = str(int(float(mid)))
    if mid_str not in master_lookup.index:
        return 5.0
    row = master_lookup.loc[mid_str]
    return float(row['weighted_score']) if 'weighted_score' in row.index else 5.0

def get_ensemble_score(mid):
    mid_str = str(int(float(mid)))
    if mid_str not in master_lookup.index:
        return 5.0
    row     = master_lookup.loc[mid_str]
    feat_df = pd.DataFrame(
        [[float(row.get(c,0)) if not isinstance(row.get(c,0), pd.Series)
          else float(row.get(c,0).iloc[0]) for c in feature_cols]],
        columns=feature_cols
    ).fillna(0)
    return float(ensemble.predict(feat_df)[0])

all_mids     = ratings['movieId'].unique().tolist()
test_by_user = test_r.groupby('userId')
sample_users = test_r['userId'].unique()[:300]

print('Pre-computing raw scores...')
user_data = []
for uid in sample_users:
    if uid not in test_by_user.groups:
        continue
    user_test   = test_by_user.get_group(uid)
    relevant    = set(user_test[user_test['rating'] >= 3.5]['movieId'].tolist())
    if not relevant:
        continue
    train_rated = set(train_r[train_r['userId'] == uid]['movieId'].tolist())
    negatives   = [m for m in all_mids if m not in train_rated and m not in relevant]
    np.random.shuffle(negatives)
    candidates  = list(relevant) + negatives[:len(relevant)*4]
    raw = []
    for m in candidates:
        c  = get_content_score(m)
        e  = get_ensemble_score(m)
        sv = svd.predict(uid, m) * (8.6/5.0)
        raw.append((m, c, sv, e))
    user_data.append((uid, relevant, raw))

print(f'Users ready: {len(user_data)}')

print('\n=== WEIGHT TUNING RESULTS ===')
print(f'{"content":>8} {"collab":>8} {"ensembl":>8} {"HitRate":>10} {"Accuracy":>10}')
print('-'*55)

best_hr = 0
best_w  = None

weight_combos = []
for wc in range(25, 60, 5):
    for wsv in range(20, 55, 5):
        we = 100 - wc - wsv
        if we < 10 or we > 40:
            continue
        weight_combos.append((wc/100, wsv/100, we/100))

for wc, wsv, we in weight_combos:
    hits, total = 0, 0
    for uid, relevant, raw in user_data:
        scores = {}
        for m, c, sv, e in raw:
            scores[m] = wc*c + wsv*sv + we*e
        top4 = set(sorted(scores, key=scores.get, reverse=True)[:4])
        if top4 & relevant:
            hits += 1
        total += 1
    hr = hits/total if total > 0 else 0
    print(f'{wc:>8.2f} {wsv:>8.2f} {we:>8.2f} {hr:>10.4f} {hr*100:>9.1f}%')
    if hr > best_hr:
        best_hr = hr
        best_w  = (wc, wsv, we)

print('\n' + '='*55)
print(f'BEST Hit Rate @ 4 : {best_hr:.4f}  ({best_hr*100:.1f}%)')
print(f'BEST weights      : content={best_w[0]:.2f}  collab={best_w[1]:.2f}  ensemble={best_w[2]:.2f}')
print('='*55)
