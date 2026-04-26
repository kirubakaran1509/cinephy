import warnings
warnings.filterwarnings("ignore")

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import pandas as pd
import numpy as np
import pickle
import scipy.sparse as sp
import shutil

from sklearn.ensemble         import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection  import train_test_split
from sklearn.metrics          import mean_squared_error
from sklearn.base             import BaseEstimator, RegressorMixin
import xgboost as xgb
from ml.pure_svd import PureSVD

PROCESSED    = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed'
SAVED_MODELS = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\ml\saved_models'
TRAINED      = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\ml\trained_models'
os.makedirs(SAVED_MODELS, exist_ok=True)

print('='*55)
print('STEP 4 - ML ENSEMBLE (RF + XGBoost + GBR)')
print('='*55)

for folder in [SAVED_MODELS, TRAINED]:
    files = os.listdir(folder) if os.path.exists(folder) else []
    print(f'{folder}:')
    for f in sorted(files): print(f'  {f}')

df = pd.read_csv(os.path.join(PROCESSED, 'master_movies.csv'))
print(f'\nMaster shape: {df.shape}')

feature_cols = [
    'budget', 'revenue', 'runtime', 'popularity',
    'rating_count', 'rating_std', 'avg_rating',
    'genre_encoded', 'language_encoded', 'year'
]
feature_cols = [c for c in feature_cols if c in df.columns]
target       = 'weighted_score'

X = df[feature_cols].copy().fillna(0)
y = df[target].copy().fillna(df[target].mean())

print(f'Features : {feature_cols}')
print(f'X shape  : {X.shape}')
print(f'y range  : {y.min():.2f} - {y.max():.2f}')

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print('\nTraining Random Forest...')
rf = RandomForestRegressor(
    n_estimators=200, max_depth=10,
    min_samples_split=5, random_state=42, n_jobs=-1
)
rf.fit(X_train, y_train)
rf_rmse = np.sqrt(mean_squared_error(y_test, rf.predict(X_test)))
print(f'RF RMSE  : {rf_rmse:.4f}')

print('Training XGBoost...')
xgb_model = xgb.XGBRegressor(
    n_estimators=200, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    random_state=42, verbosity=0,
    objective='reg:squarederror'
)
xgb_model.fit(X_train, y_train)
xgb_rmse = np.sqrt(mean_squared_error(y_test, xgb_model.predict(X_test)))
print(f'XGB RMSE : {xgb_rmse:.4f}')

print('Training Gradient Boosting...')
gbr = GradientBoostingRegressor(
    n_estimators=150, max_depth=5,
    learning_rate=0.05, random_state=42
)
gbr.fit(X_train, y_train)
gbr_rmse = np.sqrt(mean_squared_error(y_test, gbr.predict(X_test)))
print(f'GBR RMSE : {gbr_rmse:.4f}')

class WeightedEnsemble(BaseEstimator, RegressorMixin):
    def __init__(self, rf, xgb, gbr, weights=(0.40, 0.35, 0.25)):
        self.rf      = rf
        self.xgb     = xgb
        self.gbr     = gbr
        self.weights = weights
        self.feature_cols = None
    def fit(self, X, y):
        if isinstance(X, pd.DataFrame):
            self.feature_cols = list(X.columns)
        return self
    def predict(self, X):
        if not isinstance(X, pd.DataFrame):
            cols = self.feature_cols if self.feature_cols else feature_cols
            X = pd.DataFrame(X, columns=cols)
        return (self.weights[0] * self.rf.predict(X)  +
                self.weights[1] * self.xgb.predict(X) +
                self.weights[2] * self.gbr.predict(X))

ensemble = WeightedEnsemble(rf, xgb_model, gbr)
ensemble.feature_cols = feature_cols
ens_rmse = np.sqrt(mean_squared_error(y_test, ensemble.predict(X_test)))
print(f'Ensemble RMSE : {ens_rmse:.4f}')

print('\nFeature importances (RF):')
imp = pd.Series(rf.feature_importances_, index=feature_cols).sort_values(ascending=False)
for feat, val in imp.items():
    print(f'  {feat:25s} {val:.4f}')

print('\n' + '='*55)
print('COMBINED HIT RATE @ 4')
print('='*55)

tfidf_path = None
for folder in [SAVED_MODELS, TRAINED]:
    p = os.path.join(folder, 'tfidf_matrix.npz')
    if os.path.exists(p):
        tfidf_path = p
        break
print(f'tfidf_matrix found at: {tfidf_path}')

content_idx_path = None
for folder in [SAVED_MODELS, TRAINED]:
    p = os.path.join(folder, 'content_indices.pkl')
    if os.path.exists(p):
        content_idx_path = p
        break

svd_path = None
for folder in [SAVED_MODELS, TRAINED]:
    p = os.path.join(folder, 'svd_model.pkl')
    if os.path.exists(p):
        svd_path = p
        break

print(f'content_indices : {content_idx_path}')
print(f'svd_model       : {svd_path}')

tfidf_matrix = sp.load_npz(tfidf_path)
with open(content_idx_path, 'rb') as f: content_indices = pickle.load(f)
with open(svd_path,         'rb') as f: svd             = pickle.load(f)

ratings      = pd.read_csv(os.path.join(PROCESSED, 'train3_ratings_small_clean.csv'))
np.random.seed(42)
mask         = np.random.rand(len(ratings)) < 0.8
train_r      = ratings[mask]
test_r       = ratings[~mask]

df['id_str']  = df['id'].astype(str)
master_lookup = df.set_index('id_str')

# remove duplicate index entries — keep first occurrence
master_lookup = master_lookup[~master_lookup.index.duplicated(keep='first')]

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
    row      = master_lookup.loc[mid_str]
    feat_df  = pd.DataFrame(
        [[float(row.get(c, 0)) if not isinstance(row.get(c, 0), pd.Series)
          else float(row.get(c, 0).iloc[0])
          for c in feature_cols]],
        columns=feature_cols
    )
    feat_df  = feat_df.fillna(0)
    return float(ensemble.predict(feat_df)[0])

def combined_score(uid, mid):
    collab_s = svd.predict(uid, mid)
    content_s = get_content_score(mid)
    ens_s     = get_ensemble_score(mid)
    collab_n  = collab_s * (8.6 / 5.0)
    return 0.40 * content_s + 0.35 * collab_n + 0.25 * ens_s

all_mids     = ratings['movieId'].unique().tolist()
test_by_user = test_r.groupby('userId')
hits, total  = 0, 0
sample_users = test_r['userId'].unique()[:300]

print(f'Testing {len(sample_users)} users...')
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
    candidates  = list(relevant) + negatives[:len(relevant) * 4]
    scores      = {m: combined_score(uid, m) for m in candidates}
    top4        = set(sorted(scores, key=scores.get, reverse=True)[:4])
    if top4 & relevant:
        hits += 1
    total += 1

hit_rate = hits / total if total > 0 else 0
print(f'\nCombined Hit Rate @ 4 : {hit_rate:.4f}  ({hit_rate*100:.1f}%)')
print(f'Users tested          : {total}')

print('\nSaving all models...')
for fname in ['tfidf_vectorizer.pkl','tfidf_matrix.npz',
              'content_indices.pkl','movie_lookup.csv','cosine_sim.npy']:
    src = os.path.join(TRAINED, fname)
    dst = os.path.join(SAVED_MODELS, fname)
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy2(src, dst)
        print(f'  Copied {fname}')

with open(os.path.join(SAVED_MODELS, 'rf_model.pkl'),       'wb') as f: pickle.dump(rf,           f)
with open(os.path.join(SAVED_MODELS, 'xgb_model.pkl'),      'wb') as f: pickle.dump(xgb_model,    f)
with open(os.path.join(SAVED_MODELS, 'gbr_model.pkl'),      'wb') as f: pickle.dump(gbr,          f)
with open(os.path.join(SAVED_MODELS, 'ensemble_model.pkl'), 'wb') as f: pickle.dump(ensemble,     f)
with open(os.path.join(SAVED_MODELS, 'feature_cols.pkl'),   'wb') as f: pickle.dump(feature_cols, f)

print('\nAll models saved:')
for fname in sorted(os.listdir(SAVED_MODELS)):
    size = os.path.getsize(os.path.join(SAVED_MODELS, fname))
    print(f'  {fname:40s} {size/1024/1024:.2f} MB')

print('\nSTEP 4 COMPLETE')
