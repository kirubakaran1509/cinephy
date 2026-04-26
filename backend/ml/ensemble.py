import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score
from config.settings import TOP_N, CONTENT_WEIGHT, COLLAB_WEIGHT, ENSEMBLE_ML_WEIGHT

ENSEMBLE_PATH = 'ml/trained_models/ensemble_model.pkl'

def build_feature_matrix(movies_df, ratings_df):
    print('Building feature matrix for ensemble...')

    movie_stats = ratings_df.groupby('movieId').agg(
        avg_rating    = ('rating', 'mean'),
        rating_count  = ('rating', 'count'),
        rating_std    = ('rating', 'std')
    ).reset_index()
    movie_stats['movieId']    = movie_stats['movieId'].astype(str)
    movie_stats['rating_std'] = movie_stats['rating_std'].fillna(0)

    df = movies_df.copy()
    df['id'] = df['id'].astype(str)
    df = df.merge(movie_stats, left_on='id', right_on='movieId', how='left')

    df['avg_rating']   = df['avg_rating'].fillna(df['vote_average'])
    df['rating_count'] = df['rating_count'].fillna(df['vote_count'])
    df['rating_std']   = df['rating_std'].fillna(0)

    # Genre encoding
    le = LabelEncoder()
    top_genre = movies_df['genres_list'].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else 'Unknown'
    )
    df['genre_encoded'] = le.fit_transform(top_genre.fillna('Unknown'))

    # Language encoding
    df['lang_encoded'] = le.fit_transform(df['original_language'].fillna('en'))

    features = [
        'budget', 'revenue', 'runtime', 'popularity',
        'vote_average', 'vote_count', 'weighted_score',
        'avg_rating', 'rating_count', 'rating_std',
        'genre_encoded', 'lang_encoded', 'year'
    ]

    df_clean = df[features + ['weighted_score']].dropna()
    X = df_clean[features]
    y = df_clean['weighted_score']

    return X, y, df, features, le

def build_ensemble_model(movies_df, ratings_df):
    print('Building ensemble ML model (RF + XGBoost + GBR)...')

    X, y, df, features, le = build_feature_matrix(movies_df, ratings_df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Random Forest
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )

    # XGBoost
    xgb = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0
    )

    # Gradient Boosting
    gbr = GradientBoostingRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        random_state=42
    )

    # Voting Ensemble
    ensemble = VotingRegressor(estimators=[
        ('rf',  rf),
        ('xgb', xgb),
        ('gbr', gbr)
    ])

    print('Training ensemble...')
    ensemble.fit(X_train, y_train)

    y_pred = ensemble.predict(X_test)
    rmse   = np.sqrt(mean_squared_error(y_test, y_pred))
    r2     = r2_score(y_test, y_pred)
    print(f'Ensemble RMSE : {rmse:.4f}')
    print(f'Ensemble R2   : {r2:.4f}')

    with open(ENSEMBLE_PATH, 'wb') as f:
        pickle.dump({
            'model':    ensemble,
            'features': features,
            'le':       le
        }, f)

    print('Ensemble model saved.')
    return ensemble, features

def load_ensemble():
    with open(ENSEMBLE_PATH, 'rb') as f:
        return pickle.load(f)

def get_ensemble_score(movies_df, ratings_df):
    obj      = load_ensemble()
    model    = obj['model']
    features = obj['features']

    _, _, df, _, _ = build_feature_matrix(movies_df, ratings_df)
    df_feat = df[features].fillna(0)

    scores = model.predict(df_feat)
    df['ensemble_score'] = scores
    return df[['id', 'ensemble_score']]

def combine_recommendations(content_recs, collab_recs, movies_df, ratings_df, top_n=TOP_N):
    print('Combining recommendations...')

    try:
        ensemble_scores = get_ensemble_score(movies_df, ratings_df)
        ensemble_dict   = dict(zip(
            ensemble_scores['id'].astype(str),
            ensemble_scores['ensemble_score']
        ))
    except Exception as e:
        print(f'Ensemble scoring skipped: {e}')
        ensemble_dict = {}

    all_recs = {}

    for rec in content_recs:
        mid = str(rec['movieId'])
        all_recs[mid] = rec.copy()
        all_recs[mid]['content_score'] = rec.get('content_score', 0)
        all_recs[mid]['collab_score']  = 0
        all_recs[mid]['ensemble_score']= ensemble_dict.get(mid, 0)

    for rec in collab_recs:
        mid = str(rec['movieId'])
        if mid in all_recs:
            all_recs[mid]['collab_score'] = rec.get('collab_score', 0)
        else:
            all_recs[mid] = rec.copy()
            all_recs[mid]['content_score'] = 0
            all_recs[mid]['collab_score']  = rec.get('collab_score', 0)
            all_recs[mid]['ensemble_score']= ensemble_dict.get(mid, 0)

    # Normalize scores to 0-1
    def normalize(vals):
        arr = np.array(vals, dtype=float)
        mn, mx = arr.min(), arr.max()
        if mx == mn:
            return [1.0] * len(arr)
        return ((arr - mn) / (mx - mn)).tolist()

    ids             = list(all_recs.keys())
    content_scores  = normalize([all_recs[i]['content_score']  for i in ids])
    collab_scores   = normalize([all_recs[i]['collab_score']   for i in ids])
    ensemble_scores = normalize([all_recs[i]['ensemble_score'] for i in ids])

    final = []
    for idx, mid in enumerate(ids):
        rec = all_recs[mid]
        final_score = (
            CONTENT_WEIGHT     * content_scores[idx]  +
            COLLAB_WEIGHT      * collab_scores[idx]   +
            ENSEMBLE_ML_WEIGHT * ensemble_scores[idx]
        )
        rec['final_score'] = round(final_score, 4)
        final.append(rec)

    final.sort(key=lambda x: x['final_score'], reverse=True)
    return final[:top_n]
