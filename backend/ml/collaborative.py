import pickle
import numpy as np
import pandas as pd
from surprise import SVD, KNNBasic, Dataset, Reader
from surprise.model_selection import cross_validate
from config.settings import TOP_N

SVD_PATH = 'ml/trained_models/svd_model.pkl'
KNN_PATH = 'ml/trained_models/knn_model.pkl'

def build_collaborative_models(ratings_df):
    print('Building collaborative filtering models...')

    reader = Reader(rating_scale=(
        ratings_df['rating'].min(),
        ratings_df['rating'].max()
    ))

    data = Dataset.load_from_df(
        ratings_df[['userId', 'movieId', 'rating']],
        reader
    )

    trainset = data.build_full_trainset()

    # SVD model
    print('Training SVD...')
    svd = SVD(
        n_factors=150,
        n_epochs=30,
        lr_all=0.005,
        reg_all=0.02,
        random_state=42
    )
    svd.fit(trainset)

    # KNN model
    print('Training KNN...')
    knn = KNNBasic(
        k=40,
        sim_options={
            'name':        'cosine',
            'user_based':  False
        },
        verbose=False
    )
    knn.fit(trainset)

    with open(SVD_PATH, 'wb') as f:
        pickle.dump({'model': svd, 'trainset': trainset}, f)

    with open(KNN_PATH, 'wb') as f:
        pickle.dump({'model': knn, 'trainset': trainset}, f)

    print('Collaborative models saved.')
    return svd, knn, trainset

def load_svd():
    with open(SVD_PATH, 'rb') as f:
        obj = pickle.load(f)
    return obj['model'], obj['trainset']

def load_knn():
    with open(KNN_PATH, 'rb') as f:
        obj = pickle.load(f)
    return obj['model'], obj['trainset']

def get_collab_recommendations(user_id, ratings_df, movies_df, top_n=TOP_N):
    try:
        svd, trainset = load_svd()
    except Exception as e:
        print(f'SVD load error: {e}')
        return []

    # movies the user has NOT rated
    rated_movies   = set(ratings_df[ratings_df['userId'] == user_id]['movieId'].tolist())
    all_movie_ids  = set(movies_df['id'].astype(str).tolist())
    unrated_movies = list(all_movie_ids - rated_movies)

    predictions = []
    for mid in unrated_movies:
        try:
            pred = svd.predict(user_id, mid)
            predictions.append((mid, pred.est))
        except Exception:
            continue

    predictions.sort(key=lambda x: x[1], reverse=True)
    top_movie_ids = [p[0] for p in predictions[:top_n * 3]]

    results = []
    for mid in top_movie_ids:
        row = movies_df[movies_df['id'].astype(str) == str(mid)]
        if row.empty:
            continue
        row = row.iloc[0]
        pred_score = next(p[1] for p in predictions if p[0] == mid)
        results.append({
            'movieId':       str(mid),
            'title':         row['title'],
            'one_line':      row.get('one_line', ''),
            'genres':        row.get('genres', ''),
            'vote_average':  round(float(row.get('vote_average', 0)), 1),
            'year':          int(row.get('year', 0)),
            'director':      row.get('director', 'Unknown'),
            'cast':          row.get('cast_names', []),
            'producer':      row.get('producer', 'Unknown'),
            'writer':        row.get('writer', 'Unknown'),
            'collab_score':  round(float(pred_score), 4)
        })

    return results[:top_n]
