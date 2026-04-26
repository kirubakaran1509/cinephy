import warnings
warnings.filterwarnings("ignore")
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.base import BaseEstimator, RegressorMixin
import xgboost as xgb
from ml.pure_svd import PureSVD

PROCESSED    = r"C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed"
SAVED_MODELS = r"C:\Users\kirub\OneDrive\Desktop\movie\backend\ml\saved_models"

print("="*60)
print("FULL DATA AUDIT")
print("="*60)

df = pd.read_csv(os.path.join(PROCESSED, "master_movies.csv"))
print(f"master_movies.csv        : {len(df):,} movies  x  {df.shape[1]} columns")

ratings = pd.read_csv(os.path.join(PROCESSED, "train3_ratings_small_clean.csv"))
print(f"ratings_small_clean.csv  : {len(ratings):,} ratings")
print(f"  unique users           : {ratings['userId'].nunique():,}")
print(f"  unique movies rated    : {ratings['movieId'].nunique():,}")

np.random.seed(42)
mask    = np.random.rand(len(ratings)) < 0.8
train_r = ratings[mask]
test_r  = ratings[~mask]
print(f"  train split 80pct      : {len(train_r):,} rows")
print(f"  test  split 20pct      : {len(test_r):,} rows")

print()
print("="*60)
print("SAVED MODELS")
print("="*60)
for fname in sorted(os.listdir(SAVED_MODELS)):
    size = os.path.getsize(os.path.join(SAVED_MODELS, fname))
    print(f"  {fname:40s} {size/1024/1024:.2f} MB")

print()
print("="*60)
print("TRAINING SUMMARY")
print("="*60)
feature_cols = ["budget","revenue","runtime","popularity",
                "rating_count","rating_std","avg_rating",
                "genre_encoded","language_encoded","year"]
feature_cols = [c for c in feature_cols if c in df.columns]
X = df[feature_cols].fillna(0)
y = df["weighted_score"].fillna(df["weighted_score"].mean())
print(f"  Features used          : {len(feature_cols)}")
print(f"  X shape all movies     : {X.shape}")
print(f"  y range                : {y.min():.2f} - {y.max():.2f}")
print(f"  Ensemble train rows    : {int(len(X)*0.8):,}")
print(f"  Ensemble test  rows    : {len(X)-int(len(X)*0.8):,}")

print()
print("="*60)
print("CURRENT ACCURACY - Hit Rate at 4")
print("="*60)

class WeightedEnsemble(BaseEstimator, RegressorMixin):
    def __init__(self, rf, xgb, gbr, weights=(0.40,0.35,0.25)):
        self.rf=rf; self.xgb=xgb; self.gbr=gbr
        self.weights=weights; self.feature_cols=None
    def fit(self,X,y): return self
    def predict(self,X):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=feature_cols)
        return (self.weights[0]*self.rf.predict(X)+
                self.weights[1]*self.xgb.predict(X)+
                self.weights[2]*self.gbr.predict(X))

with open(os.path.join(SAVED_MODELS,"svd_model.pkl"),      "rb") as f: svd      = pickle.load(f)
with open(os.path.join(SAVED_MODELS,"ensemble_model.pkl"), "rb") as f: ensemble = pickle.load(f)

df["id_str"]  = df["id"].astype(str)
master_lookup = df.set_index("id_str")
master_lookup = master_lookup[~master_lookup.index.duplicated(keep="first")]

def get_content_score(mid):
    mid_str = str(int(float(mid)))
    if mid_str not in master_lookup.index: return 5.0
    row = master_lookup.loc[mid_str]
    return float(row["weighted_score"]) if "weighted_score" in row.index else 5.0

def get_ensemble_score(mid):
    mid_str = str(int(float(mid)))
    if mid_str not in master_lookup.index: return 5.0
    row = master_lookup.loc[mid_str]
    feat_df = pd.DataFrame(
        [[float(row.get(c,0)) if not isinstance(row.get(c,0), pd.Series)
          else float(row.get(c,0).iloc[0]) for c in feature_cols]],
        columns=feature_cols).fillna(0)
    return float(ensemble.predict(feat_df)[0])

def combined_score(uid, mid):
    sv = svd.predict(uid, mid) * (8.6/5.0)
    c  = get_content_score(mid)
    e  = get_ensemble_score(mid)
    return 0.40*c + 0.35*sv + 0.25*e

all_mids     = ratings["movieId"].unique().tolist()
test_by_user = test_r.groupby("userId")
sample_users = test_r["userId"].unique()[:300]
hits, total  = 0, 0

print(f"  Testing {len(sample_users)} users...")
for uid in sample_users:
    if uid not in test_by_user.groups: continue
    user_test   = test_by_user.get_group(uid)
    relevant    = set(user_test[user_test["rating"]>=3.5]["movieId"].tolist())
    if not relevant: continue
    train_rated = set(train_r[train_r["userId"]==uid]["movieId"].tolist())
    negatives   = [m for m in all_mids if m not in train_rated and m not in relevant]
    np.random.shuffle(negatives)
    candidates  = list(relevant)+negatives[:len(relevant)*4]
    scores      = {m:combined_score(uid,m) for m in candidates}
    top4        = set(sorted(scores,key=scores.get,reverse=True)[:4])
    if top4 & relevant: hits+=1
    total+=1

hr = hits/total if total>0 else 0
print()
print(f"  Total ratings in dataset : {len(ratings):,}")
print(f"  Trained on               : {len(train_r):,} ratings")
print(f"  Tested on                : {len(test_r):,} ratings")
print(f"  Movies in master         : {len(df):,}")
print(f"  Users tested             : {total}")
print(f"  Hits                     : {hits}")
print(f"  Hit Rate at 4            : {hr:.4f}")
print(f"  Accuracy                 : {hr*100:.1f}%")
print()
if hr >= 0.93:
    print("  STATUS: TARGET MET 93pct+")
elif hr >= 0.90:
    print("  STATUS: IN RANGE 90-93pct - good, can tune higher")
else:
    print("  STATUS: BELOW TARGET - needs fixing")
print("="*60)
