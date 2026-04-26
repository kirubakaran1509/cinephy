import pandas as pd
import numpy as np
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROCESSED   = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed'
MODELS      = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\ml\trained_models'
MASTER_PATH = os.path.join(PROCESSED, 'master_movies.csv')

print('='*55)
print('STEP 2b — REBUILD WITH MEMORY-EFFICIENT STORAGE')
print('='*55)

df = pd.read_csv(MASTER_PATH)
print(f'Loaded master: {df.shape}')

# ── TF-IDF ────────────────────────────────────────────────
print('\nFitting TF-IDF...')
tfidf = TfidfVectorizer(
    max_features=15000,
    ngram_range=(1, 2),
    stop_words='english',
    min_df=2
)
tfidf_matrix = tfidf.fit_transform(df['soup'].fillna(''))
print(f'TF-IDF matrix: {tfidf_matrix.shape}')

# ── Save tfidf matrix as float32 sparse (tiny) ────────────
# Instead of saving full cosine_sim (1800MB),
# we save the tfidf_matrix and compute per-query at runtime
# cosine_sim for ONE movie vs all = instant, uses <1MB RAM
import scipy.sparse as sp
tfidf_matrix_f32 = tfidf_matrix.astype(np.float32)
sp.save_npz(os.path.join(MODELS, 'tfidf_matrix.npz'), tfidf_matrix_f32)
print(f'Saved tfidf_matrix.npz (sparse float32)')

# ── Also save full cosine_sim as float32 numpy ────────────
# float32 cuts 1861MB -> ~930MB, still big but usable
print('\nComputing cosine_sim as float32...')
cosine_sim = cosine_similarity(tfidf_matrix, dense_output=True).astype(np.float32)
print(f'cosine_sim shape: {cosine_sim.shape}, dtype: {cosine_sim.dtype}')

# Save as numpy binary (faster + smaller than pickle)
np.save(os.path.join(MODELS, 'cosine_sim.npy'), cosine_sim)
print(f'Saved cosine_sim.npy')

# Delete old pkl if exists
old_pkl = os.path.join(MODELS, 'cosine_sim.pkl')
if os.path.exists(old_pkl):
    os.remove(old_pkl)
    print('Deleted old cosine_sim.pkl')

# ── Save other artifacts ───────────────────────────────────
with open(os.path.join(MODELS, 'tfidf_vectorizer.pkl'), 'wb') as f:
    pickle.dump(tfidf, f)

indices = pd.Series(df.index, index=df['title'].str.lower()).drop_duplicates()
with open(os.path.join(MODELS, 'content_indices.pkl'), 'wb') as f:
    pickle.dump(indices, f)

lookup_cols = ['id','title','overview','genre_list','vote_average',
               'vote_count','weighted_score','popularity','year',
               'runtime','director','cast_list','avg_rating','rating_count']
lookup_cols = [c for c in lookup_cols if c in df.columns]
df[lookup_cols].to_csv(os.path.join(MODELS, 'movie_lookup.csv'), index=False)

# ── Smoke test using tfidf_matrix (runtime approach) ──────
def get_recommendations_fast(title, n=5):
    key = title.lower()
    if key not in indices:
        return f'Not found: {title}'
    idx         = indices[key]
    query_vec   = tfidf_matrix[idx]
    sim_scores  = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = np.argsort(sim_scores)[::-1][1:n+1]
    return df[['title','vote_average','year']].iloc[top_indices]

print('\n--- Smoke test (runtime approach): Toy Story ---')
print(get_recommendations_fast('Toy Story'))
print('\n--- Smoke test: Inception ---')
print(get_recommendations_fast('Inception'))

# ── File sizes ────────────────────────────────────────────
print('\nFile sizes:')
for fname in ['tfidf_vectorizer.pkl','tfidf_matrix.npz',
              'cosine_sim.npy','content_indices.pkl','movie_lookup.csv']:
    fpath = os.path.join(MODELS, fname)
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        print(f'  {fname:35s} {size/1024/1024:.2f} MB')

print('\nSTEP 2b COMPLETE')
print('Flask will use tfidf_matrix.npz for per-query cosine sim')
print('cosine_sim.npy kept as fallback for batch operations')
