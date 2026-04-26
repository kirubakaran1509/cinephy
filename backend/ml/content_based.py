import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config.settings import TOP_N

MODEL_PATH = 'ml/trained_models/content_model.pkl'

def build_content_model(df):
    print('Building content-based model...')
    tfidf = TfidfVectorizer(
        stop_words='english',
        max_features=15000,
        ngram_range=(1, 2)
    )
    tfidf_matrix = tfidf.fit_transform(df['soup'].fillna(''))
    cosine_sim   = cosine_similarity(tfidf_matrix, tfidf_matrix)

    indices = pd.Series(df.index, index=df['title'].str.lower()).drop_duplicates()

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump({
            'cosine_sim': cosine_sim,
            'indices':    indices,
            'titles':     df['title'].values,
            'movie_ids':  df['id'].values
        }, f)

    print('Content model saved.')
    return cosine_sim, indices

def load_content_model():
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)

def get_content_recommendations(title, df, top_n=TOP_N):
    model      = load_content_model()
    cosine_sim = model['cosine_sim']
    indices    = model['indices']

    title_lower = title.lower().strip()

    if title_lower not in indices:
        # fuzzy fallback
        matches = [t for t in indices.index if title_lower in t]
        if not matches:
            return []
        title_lower = matches[0]

    idx  = indices[title_lower]
    sims = list(enumerate(cosine_sim[idx]))
    sims = sorted(sims, key=lambda x: x[1], reverse=True)
    sims = [s for s in sims if s[0] != idx][:top_n * 3]

    results = []
    for i, score in sims:
        row = df.iloc[i]
        results.append({
            'movieId':       str(row.get('id', '')),
            'title':         row['title'],
            'one_line':      row.get('one_line', ''),
            'genres':        row.get('genres', ''),
            'vote_average':  round(float(row.get('vote_average', 0)), 1),
            'year':          int(row.get('year', 0)),
            'director':      row.get('director', 'Unknown'),
            'cast':          row.get('cast_names', []),
            'producer':      row.get('producer', 'Unknown'),
            'writer':        row.get('writer', 'Unknown'),
            'content_score': round(float(score), 4)
        })

    return results[:top_n]
