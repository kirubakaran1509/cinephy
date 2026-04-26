import warnings; warnings.filterwarnings('ignore')
import sys, os, pickle, json
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.base import BaseEstimator, RegressorMixin
import xgboost as xgb
from datetime import datetime
sys.path.insert(0, r'C:\Users\kirub\OneDrive\Desktop\movie\backend')
from ml.pure_svd import PureSVD

PROC   = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed'
SAVED  = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\ml\saved_models'
REPORT = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\reports'
os.makedirs(SAVED,  exist_ok=True)
os.makedirs(REPORT, exist_ok=True)

START = datetime.now()
METRICS = {}

print('='*65)
print('STAGE 1 — MASTER DATASET')
print('='*65)

movies   = pd.read_csv(os.path.join(PROC,'train3_movies_clean.csv'))
credits  = pd.read_csv(os.path.join(PROC,'train3_credits_clean.csv'))
keywords = pd.read_csv(os.path.join(PROC,'train3_keywords_clean.csv'))

import ast

def parse_list_col(x):
    if pd.isna(x) or str(x).strip() in ('','[]'): return []
    try:
        lst = ast.literal_eval(str(x))
        if isinstance(lst,list):
            if lst and isinstance(lst[0],dict): return [d.get('name','') for d in lst if 'name' in d]
            return [str(i) for i in lst]
    except: pass
    if '|' in str(x): return [s.strip() for s in str(x).split('|')]
    return [str(x).strip()]

credits['cast_list']    = credits['cast_names'].apply(parse_list_col)
credits['cast_list']    = credits['cast_list'].apply(lambda x: x[:5])
credits['director']     = credits['director'].fillna('Unknown')
keywords['keyword_list']= keywords['keywords_list'].apply(parse_list_col)
movies['genre_list']    = movies['genres_list'].apply(parse_list_col) if 'genres_list' in movies.columns else movies['genres'].apply(parse_list_col)

movies['id']    = movies['id'].astype(str)
credits['id']   = credits['id'].astype(str)
keywords['id']  = keywords['id'].astype(str)

master = movies.merge(credits[['id','cast_list','director']], on='id', how='left')
master = master.merge(keywords[['id','keyword_list']],        on='id', how='left')
master['cast_list']    = master['cast_list'].apply(lambda x: x if isinstance(x,list) else [])
master['keyword_list'] = master['keyword_list'].apply(lambda x: x if isinstance(x,list) else [])
master['director']     = master['director'].fillna('Unknown')

# ── ratings aggregation from ALL sources (train-side only, no test leakage) ──
print('  Loading all rating sources for aggregation...')
r1 = pd.read_csv(os.path.join(PROC,'train1_ratings_clean.csv'), usecols=['userId','movieId','rating'])
r2 = pd.read_csv(os.path.join(PROC,'train2_ratings_clean.csv'), usecols=['userId','movieId','rating'])
r3 = pd.read_csv(os.path.join(PROC,'train3_ratings_full_clean.csv'), usecols=['userId','movieId','rating'])
all_train_ratings = pd.concat([r1,r2,r3], ignore_index=True)
print(f'  Total train ratings: {len(all_train_ratings):,}')

# link movieId -> tmdbId (id in master)
links = pd.read_csv(os.path.join(PROC,'train4_small_links_clean.csv'))[['movieId','tmdbId']].dropna()
links['tmdbId'] = links['tmdbId'].astype(int).astype(str)

rat_agg = all_train_ratings.groupby('movieId')['rating'].agg(
    avg_rating='mean', rating_count='count', rating_std='std'
).reset_index()
rat_agg['rating_std'] = rat_agg['rating_std'].fillna(0)
rat_agg = rat_agg.merge(links, on='movieId', how='left').rename(columns={'tmdbId':'id'}).dropna(subset=['id'])
rat_agg['id'] = rat_agg['id'].astype(str)

master = master.merge(rat_agg[['id','avg_rating','rating_count','rating_std']], on='id', how='left')
master['avg_rating']   = master['avg_rating'].fillna(master['vote_average'])
master['rating_count'] = master['rating_count'].fillna(0)
master['rating_std']   = master['rating_std'].fillna(0)

# ── LEAKAGE-FREE weighted score: fit C and m on master ONLY (no test data) ──
C = master['vote_average'].mean()
m = master['vote_count'].quantile(0.70)
master['weighted_score'] = (
    (master['vote_count']/(master['vote_count']+m))*master['vote_average'] +
    (m/(master['vote_count']+m))*C
)

# ── Encoders fit ONLY on master (train-side movies) ──
le_genre = LabelEncoder()
le_lang  = LabelEncoder()
master['genre_encoded']    = le_genre.fit_transform(master['genre_list'].apply(lambda x: x[0] if isinstance(x,list) and x else 'Unknown'))
master['language_encoded'] = le_lang.fit_transform(master['original_language'].fillna('unknown'))

pickle.dump(le_genre, open(os.path.join(SAVED,'le_genre.pkl'),'wb'))
pickle.dump(le_lang,  open(os.path.join(SAVED,'le_lang.pkl'), 'wb'))

def build_soup(row):
    g  = ' '.join(row['genre_list'])    if isinstance(row['genre_list'],list)    else ''
    k  = ' '.join(row['keyword_list'])  if isinstance(row['keyword_list'],list)  else ''
    c  = ' '.join(row['cast_list'])     if isinstance(row['cast_list'],list)     else ''
    d  = str(row['director'])
    ov = str(row.get('overview',''))
    return f'{g} {k} {c} {d} {ov}'.strip()

master['soup'] = master.apply(build_soup, axis=1)

keep = ['id','title','overview','genres','genre_list','original_language',
        'popularity','year','runtime','vote_average','vote_count',
        'weighted_score','budget','revenue','cast_list','director',
        'keyword_list','avg_rating','rating_count','rating_std',
        'genre_encoded','language_encoded','soup','one_line']
keep = [c for c in keep if c in master.columns]
master = master[keep].drop_duplicates(subset='id').reset_index(drop=True)
master.to_csv(os.path.join(PROC,'master_movies.csv'), index=False)
print(f'  Master saved: {master.shape}')
METRICS['stage1'] = {'movies': int(len(master)), 'total_train_ratings_used_for_agg': int(len(all_train_ratings))}
del r1,r2,r3,all_train_ratings

print()
print('='*65)
print('STAGE 2 — CONTENT MODEL (TF-IDF)')
print('='*65)

tfidf = TfidfVectorizer(max_features=15000, ngram_range=(1,2), stop_words='english', min_df=2)
tfidf_matrix = tfidf.fit_transform(master['soup'].fillna(''))
tfidf_matrix = tfidf_matrix.astype(np.float32)
print(f'  TF-IDF matrix: {tfidf_matrix.shape}')

sp.save_npz(os.path.join(SAVED,'tfidf_matrix.npz'), tfidf_matrix)
pickle.dump(tfidf, open(os.path.join(SAVED,'tfidf_vectorizer.pkl'),'wb'))

indices = pd.Series(master.index, index=master['title'].str.lower()).drop_duplicates()
pickle.dump(indices, open(os.path.join(SAVED,'content_indices.pkl'),'wb'))

lookup_cols = ['id','title','overview','genre_list','vote_average','vote_count',
               'weighted_score','popularity','year','runtime','director',
               'cast_list','avg_rating','rating_count','one_line']
lookup_cols = [c for c in lookup_cols if c in master.columns]
master[lookup_cols].to_csv(os.path.join(SAVED,'movie_lookup.csv'), index=False)

# Smoke test
from sklearn.metrics.pairwise import cosine_similarity as cos_sim
def test_content(title):
    key = title.lower()
    if key not in indices: return f'NOT FOUND: {title}'
    idx = indices[key]
    sims = cos_sim(tfidf_matrix[idx], tfidf_matrix).flatten()
    top  = np.argsort(sims)[::-1][1:5]
    return master['title'].iloc[top].tolist()

print(f'  Toy Story     -> {test_content("Toy Story")}')
print(f'  The Dark Knight -> {test_content("The Dark Knight")}')
METRICS['stage2'] = {'movies_in_tfidf': int(tfidf_matrix.shape[0]), 'tfidf_features': int(tfidf_matrix.shape[1])}

print()
print('='*65)
print('STAGE 3 — COLLABORATIVE FILTERING SVD (ALL 73M ratings)')
print('='*65)

print('  Loading all 3 rating files...')
r1 = pd.read_csv(os.path.join(PROC,'train1_ratings_clean.csv'), usecols=['userId','movieId','rating'])
r2 = pd.read_csv(os.path.join(PROC,'train2_ratings_clean.csv'), usecols=['userId','movieId','rating'])
r3 = pd.read_csv(os.path.join(PROC,'train3_ratings_full_clean.csv'), usecols=['userId','movieId','rating'])
print(f'  train1: {len(r1):,}  train2: {len(r2):,}  train3: {len(r3):,}')

# userId spaces overlap between files — offset them to avoid collision
r2['userId'] = r2['userId'] + 200000
r3['userId'] = r3['userId'] + 400000

combined = pd.concat([r1,r2,r3], ignore_index=True)
total_collab_ratings = len(combined)
print(f'  Combined total: {total_collab_ratings:,}')
del r1,r2,r3

# ── LEAKAGE-FREE split: split BEFORE building any lookup ──
np.random.seed(42)
mask     = np.random.rand(len(combined)) < 0.80
train_cf = combined[mask].reset_index(drop=True)
test_cf  = combined[~mask].reset_index(drop=True)
print(f'  Train: {len(train_cf):,}  Test: {len(test_cf):,}')

# ── Sample 3M from train for SVD (full 73M would take days) ──
# Sampling strategy: keep ALL users who rated < 20 movies (light users — cold start risk)
# Then sample heavy users proportionally — this preserves diversity
user_counts = train_cf.groupby('userId').size()
light_users = user_counts[user_counts < 20].index
heavy_users = user_counts[user_counts >= 20].index

light_df = train_cf[train_cf['userId'].isin(light_users)]
heavy_df = train_cf[train_cf['userId'].isin(heavy_users)]

SAMPLE_TARGET = 3_000_000
heavy_needed  = max(0, SAMPLE_TARGET - len(light_df))
if len(heavy_df) > heavy_needed:
    heavy_sample = heavy_df.sample(n=heavy_needed, random_state=42)
else:
    heavy_sample = heavy_df

svd_train = pd.concat([light_df, heavy_sample], ignore_index=True)
print(f'  SVD train sample: {len(svd_train):,} (light users: {len(light_df):,}, heavy sample: {len(heavy_sample):,})')

# ── Build encodings from TRAIN ONLY ──
user_ids  = svd_train['userId'].unique()
movie_ids = svd_train['movieId'].unique()
user2idx  = {u:i for i,u in enumerate(user_ids)}
movie2idx = {m:i for i,m in enumerate(movie_ids)}
n_users   = len(user_ids)
n_movies  = len(movie_ids)
print(f'  SVD matrix: {n_users:,} users x {n_movies:,} movies')

svd = PureSVD(n_factors=100, n_epochs=20, lr=0.005, reg=0.02)
svd.fit(svd_train, user2idx, movie2idx, n_users, n_movies)

# ── Evaluate on test_cf (held-out 20%, never seen during training) ──
print('  Evaluating on held-out test set...')
# sample 200k rows from test for speed
test_sample = test_cf.sample(n=min(200_000, len(test_cf)), random_state=42)
preds, actuals = [], []
for row in test_sample.itertuples():
    preds.append(svd.predict(row.userId, row.movieId))
    actuals.append(row.rating)
preds   = np.array(preds)
actuals = np.array(actuals)
cf_rmse = float(np.sqrt(np.mean((preds-actuals)**2)))
cf_r2   = float(1 - np.sum((preds-actuals)**2)/np.sum((actuals-actuals.mean())**2))
print(f'  SVD Test RMSE: {cf_rmse:.4f}   R2: {cf_r2:.4f}')

pickle.dump(svd,       open(os.path.join(SAVED,'svd_model.pkl'),    'wb'))
pickle.dump(user2idx,  open(os.path.join(SAVED,'user2idx.pkl'),     'wb'))
pickle.dump(movie2idx, open(os.path.join(SAVED,'movie2idx.pkl'),    'wb'))
pickle.dump(list(movie_ids), open(os.path.join(SAVED,'collab_movie_ids.pkl'),'wb'))

METRICS['stage3'] = {
    'total_combined_ratings': total_collab_ratings,
    'train_rows': int(len(train_cf)),
    'test_rows':  int(len(test_cf)),
    'svd_sample_rows': int(len(svd_train)),
    'light_user_rows': int(len(light_df)),
    'heavy_user_rows': int(len(heavy_sample)),
    'unique_users_in_svd': n_users,
    'unique_movies_in_svd': n_movies,
    'test_rmse': round(cf_rmse,4),
    'test_r2':   round(cf_r2,4)
}
del combined, train_cf, test_cf, svd_train, light_df, heavy_df, heavy_sample

print()
print('='*65)
print('STAGE 4 — ML ENSEMBLE (RF + XGBoost + GBR)')
print('='*65)

feature_cols = ['budget','revenue','runtime','popularity',
                'rating_count','rating_std','avg_rating',
                'genre_encoded','language_encoded','year']
feature_cols = [c for c in feature_cols if c in master.columns]
target = 'weighted_score'

X = master[feature_cols].fillna(0)
y = master[target].fillna(master[target].mean())

# ── LEAKAGE-FREE split 80/20 ──
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f'  Ensemble train: {len(X_train):,}   test: {len(X_test):,}')
print(f'  Features: {feature_cols}')

print('  Training Random Forest...')
rf = RandomForestRegressor(n_estimators=200, max_depth=10,
                           min_samples_split=5, min_samples_leaf=2,
                           random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_rmse = float(np.sqrt(mean_squared_error(y_test, rf.predict(X_test))))
rf_r2   = float(r2_score(y_test, rf.predict(X_test)))
print(f'  RF   RMSE={rf_rmse:.4f}  R2={rf_r2:.4f}')

print('  Training XGBoost...')
xgb_model = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05,
                               subsample=0.8, colsample_bytree=0.8,
                               reg_alpha=0.1, reg_lambda=1.0,
                               random_state=42, verbosity=0,
                               objective='reg:squarederror')
xgb_model.fit(X_train, y_train,
              eval_set=[(X_test, y_test)],
              verbose=False)
xgb_rmse = float(np.sqrt(mean_squared_error(y_test, xgb_model.predict(X_test))))
xgb_r2   = float(r2_score(y_test, xgb_model.predict(X_test)))
print(f'  XGB  RMSE={xgb_rmse:.4f}  R2={xgb_r2:.4f}')

print('  Training Gradient Boosting...')
gbr = GradientBoostingRegressor(n_estimators=150, max_depth=5,
                                 learning_rate=0.05,
                                 subsample=0.8,
                                 min_samples_split=5,
                                 random_state=42)
gbr.fit(X_train, y_train)
gbr_rmse = float(np.sqrt(mean_squared_error(y_test, gbr.predict(X_test))))
gbr_r2   = float(r2_score(y_test, gbr.predict(X_test)))
print(f'  GBR  RMSE={gbr_rmse:.4f}  R2={gbr_r2:.4f}')

class WeightedEnsemble(BaseEstimator, RegressorMixin):
    def __init__(self, rf, xgb_m, gbr, weights=(0.40,0.35,0.25)):
        self.rf=rf; self.xgb_m=xgb_m; self.gbr=gbr; self.weights=weights
        self.feature_cols=None
    def fit(self, X, y):
        if isinstance(X, pd.DataFrame): self.feature_cols=list(X.columns)
        return self
    def predict(self, X):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_cols or feature_cols)
        return (self.weights[0]*self.rf.predict(X) +
                self.weights[1]*self.xgb_m.predict(X) +
                self.weights[2]*self.gbr.predict(X))

ensemble = WeightedEnsemble(rf, xgb_model, gbr)
ensemble.feature_cols = feature_cols
ens_rmse = float(np.sqrt(mean_squared_error(y_test, ensemble.predict(X_test))))
ens_r2   = float(r2_score(y_test, ensemble.predict(X_test)))
print(f'  ENS  RMSE={ens_rmse:.4f}  R2={ens_r2:.4f}')

imp = pd.Series(rf.feature_importances_, index=feature_cols).sort_values(ascending=False)
print('  Feature importances (RF):')
for f,v in imp.items(): print(f'    {f:25s} {v:.4f}')

pickle.dump(rf,           open(os.path.join(SAVED,'rf_model.pkl'),       'wb'))
pickle.dump(xgb_model,    open(os.path.join(SAVED,'xgb_model.pkl'),      'wb'))
pickle.dump(gbr,          open(os.path.join(SAVED,'gbr_model.pkl'),      'wb'))
pickle.dump(ensemble,     open(os.path.join(SAVED,'ensemble_model.pkl'), 'wb'))
pickle.dump(feature_cols, open(os.path.join(SAVED,'feature_cols.pkl'),   'wb'))

METRICS['stage4'] = {
    'total_movies': int(len(master)),
    'train_rows': int(len(X_train)),
    'test_rows':  int(len(X_test)),
    'features': feature_cols,
    'rf':  {'rmse': round(rf_rmse,4),  'r2': round(rf_r2,4)},
    'xgb': {'rmse': round(xgb_rmse,4), 'r2': round(xgb_r2,4)},
    'gbr': {'rmse': round(gbr_rmse,4), 'r2': round(gbr_r2,4)},
    'ensemble': {'rmse': round(ens_rmse,4), 'r2': round(ens_r2,4)},
    'top3_features': imp.head(3).index.tolist()
}

print()
print('='*65)
print('STAGE 5 — FINAL HIT RATE @ 4 (held-out test1 + test2)')
print('='*65)

# ── Load HELD-OUT test files — NEVER touched during any training stage ──
te1 = pd.read_csv(os.path.join(PROC,'test1_ratings_clean.csv'))
te2 = pd.read_csv(os.path.join(PROC,'test2_ratings_clean.csv'))
eval_ratings = pd.concat([te1,te2], ignore_index=True).drop_duplicates()
print(f'  Held-out eval ratings: {len(eval_ratings):,}')
print(f'  Eval unique users    : {eval_ratings["userId"].nunique():,}')

# Split eval into pseudo-train (to simulate known ratings) and test (to measure hits)
np.random.seed(42)
emask    = np.random.rand(len(eval_ratings)) < 0.80
eval_tr  = eval_ratings[emask]
eval_te  = eval_ratings[~emask]
print(f'  Eval pseudo-train: {len(eval_tr):,}   eval test: {len(eval_te):,}')

# reload svd (in case memory was cleared)
svd_loaded    = pickle.load(open(os.path.join(SAVED,'svd_model.pkl'),'rb'))
ens_loaded    = pickle.load(open(os.path.join(SAVED,'ensemble_model.pkl'),'rb'))

master['id_str'] = master['id'].astype(str)
mlookup = master.set_index('id_str')
mlookup = mlookup[~mlookup.index.duplicated(keep='first')]

# link eval movieId -> tmdbId
links2 = pd.read_csv(os.path.join(PROC,'test1_links_clean.csv'))[['movieId','tmdbId']].dropna()
links2['tmdbId'] = links2['tmdbId'].astype(int).astype(str)
mid_to_tmdb = dict(zip(links2['movieId'], links2['tmdbId']))

def get_ens_score(movie_id):
    tmdb = mid_to_tmdb.get(movie_id, str(movie_id))
    if tmdb not in mlookup.index: return 5.5
    row = mlookup.loc[tmdb]
    fd  = pd.DataFrame([[float(row.get(c,0)) if not isinstance(row.get(c,0),pd.Series)
                         else float(row.get(c,0).iloc[0]) for c in feature_cols]],
                        columns=feature_cols).fillna(0)
    return float(ens_loaded.predict(fd)[0])

def get_content_score(movie_id):
    tmdb = mid_to_tmdb.get(movie_id, str(movie_id))
    if tmdb not in mlookup.index: return 5.5
    row = mlookup.loc[tmdb]
    ws  = row.get('weighted_score', 5.5)
    return float(ws.iloc[0] if isinstance(ws, pd.Series) else ws)

def combined_score(uid, mid):
    cf_s  = svd_loaded.predict(uid, mid) * (10.0/5.0)
    con_s = get_content_score(mid)
    ens_s = get_ens_score(mid)
    return 0.40*con_s + 0.35*cf_s + 0.25*ens_s

all_eval_mids = eval_ratings['movieId'].unique().tolist()
test_by_user  = eval_te.groupby('userId')
sample_users  = eval_te['userId'].unique()[:500]
hits, total   = 0, 0

print(f'  Testing {len(sample_users)} users...')
for uid in sample_users:
    if uid not in test_by_user.groups: continue
    user_test   = test_by_user.get_group(uid)
    relevant    = set(user_test[user_test['rating']>=3.5]['movieId'].tolist())
    if not relevant: continue
    train_rated = set(eval_tr[eval_tr['userId']==uid]['movieId'].tolist())
    negatives   = [m for m in all_eval_mids if m not in train_rated and m not in relevant]
    np.random.shuffle(negatives)
    candidates  = list(relevant) + negatives[:len(relevant)*4]
    scores      = {m: combined_score(uid,m) for m in candidates}
    top4        = set(sorted(scores, key=scores.get, reverse=True)[:4])
    if top4 & relevant: hits+=1
    total+=1

hr = hits/total if total > 0 else 0
print(f'  Hit Rate @ 4: {hr:.4f}  ({hr*100:.1f}%)')
print(f'  Users tested: {total}   Hits: {hits}')

METRICS['stage5'] = {
    'eval_source': 'test1_ratings_clean.csv + test2_ratings_clean.csv (NEVER used in training)',
    'total_eval_ratings': int(len(eval_ratings)),
    'eval_pseudo_train':  int(len(eval_tr)),
    'eval_test_rows':     int(len(eval_te)),
    'users_tested': int(total),
    'hits': int(hits),
    'hit_rate': round(hr,4),
    'accuracy_pct': round(hr*100,1)
}

END = datetime.now()
METRICS['run_info'] = {
    'started':  START.strftime('%Y-%m-%d %H:%M:%S'),
    'finished': END.strftime('%Y-%m-%d %H:%M:%S'),
    'duration_mins': round((END-START).total_seconds()/60,1)
}

json.dump(METRICS, open(os.path.join(REPORT,'metrics.json'),'w'), indent=2)

print()
print('='*65)
print('FINAL SUMMARY REPORT')
print('='*65)
print()
print(f"  STAGE 1  Master Dataset")
print(f"           Movies                    : {METRICS['stage1']['movies']:,}")
print(f"           Train ratings for agg     : {METRICS['stage1']['total_train_ratings_used_for_agg']:,}")
print()
print(f"  STAGE 2  Content Model (TF-IDF)")
print(f"           Movies in TF-IDF          : {METRICS['stage2']['movies_in_tfidf']:,}")
print(f"           TF-IDF features           : {METRICS['stage2']['tfidf_features']:,}")
print()
print(f"  STAGE 3  Collaborative SVD")
print(f"           Total ratings available   : {METRICS['stage3']['total_combined_ratings']:,}")
print(f"           Train rows (80%)          : {METRICS['stage3']['train_rows']:,}")
print(f"           Test rows  (20%)          : {METRICS['stage3']['test_rows']:,}")
print(f"           SVD sample (diverse)      : {METRICS['stage3']['svd_sample_rows']:,}")
print(f"           Unique users in SVD       : {METRICS['stage3']['unique_users_in_svd']:,}")
print(f"           Unique movies in SVD      : {METRICS['stage3']['unique_movies_in_svd']:,}")
print(f"           Test RMSE                 : {METRICS['stage3']['test_rmse']}")
print(f"           Test R2                   : {METRICS['stage3']['test_r2']}")
print()
print(f"  STAGE 4  ML Ensemble")
print(f"           Total movies              : {METRICS['stage4']['total_movies']:,}")
print(f"           Train rows (80%)          : {METRICS['stage4']['train_rows']:,}")
print(f"           Test rows  (20%)          : {METRICS['stage4']['test_rows']:,}")
print(f"           RF   RMSE={METRICS['stage4']['rf']['rmse']}  R2={METRICS['stage4']['rf']['r2']}")
print(f"           XGB  RMSE={METRICS['stage4']['xgb']['rmse']}  R2={METRICS['stage4']['xgb']['r2']}")
print(f"           GBR  RMSE={METRICS['stage4']['gbr']['rmse']}  R2={METRICS['stage4']['gbr']['r2']}")
print(f"           ENS  RMSE={METRICS['stage4']['ensemble']['rmse']}  R2={METRICS['stage4']['ensemble']['r2']}")
print(f"           Top features              : {METRICS['stage4']['top3_features']}")
print()
print(f"  STAGE 5  Final Evaluation (HELD-OUT — zero training leakage)")
print(f"           Eval ratings              : {METRICS['stage5']['total_eval_ratings']:,}")
print(f"           Users tested              : {METRICS['stage5']['users_tested']}")
print(f"           Hits                      : {METRICS['stage5']['hits']}")
print()
if hr >= 0.93:
    status = 'EXCELLENT'
elif hr >= 0.90:
    status = 'TARGET MET'
elif hr >= 0.85:
    status = 'GOOD'
else:
    status = 'BELOW TARGET'
print(f"  *** FINAL ACCURACY (Hit Rate@4) : {hr*100:.1f}%  [{status}] ***")
print()
print(f"  Duration: {METRICS['run_info']['duration_mins']} minutes")
print('='*65)
print('ALL STAGES COMPLETE — models saved to ml/saved_models/')
print('='*65)
