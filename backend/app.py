import warnings
warnings.filterwarnings('ignore')
import os, pickle, ast
import numpy as np
import pandas as pd
import scipy.sparse as sp
from flask import Flask
from flask_cors import CORS
from sklearn.base import BaseEstimator, RegressorMixin

app = Flask(__name__)
CORS(app)

PROC  = os.path.join(os.path.dirname(__file__), 'data', 'processed')
SAVED = os.path.join(os.path.dirname(__file__), 'ml', 'saved_models')

class WeightedEnsemble(BaseEstimator, RegressorMixin):
    def __init__(self, rf, xgb_m, gbr, weights=(0.40, 0.35, 0.25)):
        self.rf = rf
        self.xgb_m = xgb_m
        self.gbr = gbr
        self.weights = weights
        self.feature_cols = None
    def fit(self, X, y):
        if isinstance(X, pd.DataFrame):
            self.feature_cols = list(X.columns)
        return self
    def predict(self, X):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_cols)
        return (self.weights[0] * self.rf.predict(X) +
                self.weights[1] * self.xgb_m.predict(X) +
                self.weights[2] * self.gbr.predict(X))

print('Loading models...')
from ml.pure_svd import PureSVD

# Load all models EXCEPT svd (lazy load later)
rf      = pickle.load(open(os.path.join(SAVED, 'rf_model.pkl'),         'rb'))
xgb_m   = pickle.load(open(os.path.join(SAVED, 'xgb_model.pkl'),        'rb'))
gbr     = pickle.load(open(os.path.join(SAVED, 'gbr_model.pkl'),         'rb'))
feat    = pickle.load(open(os.path.join(SAVED, 'feature_cols.pkl'),      'rb'))
tfidf_v = pickle.load(open(os.path.join(SAVED, 'tfidf_vectorizer.pkl'),  'rb'))
indices = pickle.load(open(os.path.join(SAVED, 'content_indices.pkl'),   'rb'))
tfidf_m = sp.load_npz(os.path.join(SAVED, 'tfidf_matrix.npz'))

ensemble = WeightedEnsemble(rf, xgb_m, gbr)
ensemble.feature_cols = feat

master   = pd.read_csv(os.path.join(PROC, 'master_movies.csv'))
master['id_str'] = master['id'].astype(str)
mlookup  = master.set_index('id_str')
mlookup  = mlookup[~mlookup.index.duplicated(keep='first')]

links    = pd.read_csv(os.path.join(PROC, 'test1_links_clean.csv'))[['movieId','tmdbId']].dropna()
links['tmdbId'] = links['tmdbId'].astype(int).astype(str)
mid_to_tmdb = dict(zip(links['movieId'], links['tmdbId']))

print('Pre-caching scores...')
all_mids      = master['id'].tolist()
content_cache = {}
ens_cache     = {}
feat_rows     = []
valid_mids    = []

for mid in all_mids:
    mid_str = str(mid)
    if mid_str in mlookup.index:
        row = mlookup.loc[mid_str]
        ws  = row.get('weighted_score', 5.5)
        content_cache[mid_str] = float(ws.iloc[0] if isinstance(ws, pd.Series) else ws)
        feat_rows.append([
            float(row.get(c, 0)) if not isinstance(row.get(c, 0), pd.Series)
            else float(row.get(c, 0).iloc[0]) for c in feat
        ])
        valid_mids.append(mid_str)
    else:
        content_cache[mid_str] = 5.5
        ens_cache[mid_str]     = 5.5

if feat_rows:
    fd_all    = pd.DataFrame(feat_rows, columns=feat).fillna(0)
    ens_preds = ensemble.predict(fd_all)
    for mid_str, score in zip(valid_mids, ens_preds):
        ens_cache[mid_str] = float(score)

# SVD loaded lazily on first user-based request
svd = None

def get_svd():
    global svd
    if svd is None:
        print('Loading SVD model on demand...')
        svd = pickle.load(open(os.path.join(SAVED, 'svd_model.pkl'), 'rb'))
        print('SVD loaded.')
    return svd

print('All caches ready.')

from routes.recommend import recommend_bp
from routes.movie     import movie_bp
from routes.user      import user_bp

app.register_blueprint(recommend_bp)
app.register_blueprint(movie_bp)
app.register_blueprint(user_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
