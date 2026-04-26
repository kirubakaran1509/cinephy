import pandas as pd
import numpy as np
import ast
import os
from sklearn.preprocessing import LabelEncoder

PROCESSED = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed'
MASTER_OUT = os.path.join(PROCESSED, 'master_movies.csv')

print('='*55)
print('STEP 1 — REBUILDING MASTER WITH CORRECT CREDITS')
print('='*55)

movies   = pd.read_csv(os.path.join(PROCESSED, 'train3_movies_clean.csv'))
credits  = pd.read_csv(os.path.join(PROCESSED, 'train3_credits_clean.csv'))
keywords = pd.read_csv(os.path.join(PROCESSED, 'train3_keywords_clean.csv'))
ratings  = pd.read_csv(os.path.join(PROCESSED, 'train3_ratings_small_clean.csv'))

print(f'Credits columns  : {list(credits.columns)}')
print(f'Credits sample:')
print(credits.head(2).to_string())

# ── credits — already parsed, use directly ────────────────
# cast_names is a plain string like "Tom Hanks|Tim Allen" or similar
# director is already its own column
def parse_cast_names(x):
    if pd.isna(x) or x == '' or x == '[]':
        return []
    # try pipe-separated
    if '|' in str(x):
        return [n.strip() for n in str(x).split('|')][:5]
    # try comma-separated
    if ',' in str(x):
        return [n.strip() for n in str(x).split(',')][:5]
    # try ast list
    try:
        lst = ast.literal_eval(x)
        if isinstance(lst, list):
            if len(lst) > 0 and isinstance(lst[0], dict):
                return [m['name'] for m in lst[:5] if 'name' in m]
            return [str(m) for m in lst[:5]]
    except:
        pass
    # single name
    return [str(x).strip()] if str(x).strip() else []

credits['cast_list'] = credits['cast_names'].apply(parse_cast_names)
credits['director']  = credits['director'].fillna('')

print(f'\nSample cast_list after parse:')
print(credits['cast_list'].head(5).tolist())
print(f'Sample director:')
print(credits['director'].head(5).tolist())

credits_clean = credits[['id', 'cast_list', 'director']].copy()

# ── keywords — already a list string ─────────────────────
def parse_keyword_list(x):
    if pd.isna(x) or x == '':
        return []
    try:
        lst = ast.literal_eval(x)
        if isinstance(lst, list):
            if len(lst) > 0 and isinstance(lst[0], dict):
                return [m['name'] for m in lst if 'name' in m]
            return [str(m) for m in lst]
    except:
        pass
    return []

keywords['keyword_list'] = keywords['keywords_list'].apply(parse_keyword_list)
keywords_clean = keywords[['id', 'keyword_list']].copy()

# ── genres ────────────────────────────────────────────────
def parse_genre_list(x):
    if pd.isna(x) or x == '':
        return []
    try:
        lst = ast.literal_eval(x)
        if isinstance(lst, list):
            if len(lst) > 0 and isinstance(lst[0], dict):
                return [m['name'] for m in lst if 'name' in m]
            return [str(m) for m in lst]
    except:
        pass
    return []

# movies already has genres_list column — use it directly
if 'genres_list' in movies.columns:
    movies['genre_list'] = movies['genres_list'].apply(
        lambda x: x if isinstance(x, list) else parse_genre_list(str(x))
    )
else:
    movies['genre_list'] = movies['genres'].apply(parse_genre_list)

# ── merge ─────────────────────────────────────────────────
movies['id']         = movies['id'].astype(str)
credits_clean['id']  = credits_clean['id'].astype(str)
keywords_clean['id'] = keywords_clean['id'].astype(str)

master = movies.merge(credits_clean,  on='id', how='left')
master = master.merge(keywords_clean, on='id', how='left')

master['cast_list']    = master['cast_list'].apply(lambda x: x if isinstance(x, list) else [])
master['keyword_list'] = master['keyword_list'].apply(lambda x: x if isinstance(x, list) else [])
master['director']     = master['director'].fillna('')

print(f'\nAfter merge       : {master.shape}')
print(f'Sample cast_list  : {master["cast_list"].head(3).tolist()}')
print(f'Sample director   : {master["director"].head(3).tolist()}')
print(f'Sample keywords   : {master["keyword_list"].head(2).tolist()}')

# ── ratings ───────────────────────────────────────────────
rat_agg = ratings.groupby('movieId')['rating'].agg(
    avg_rating='mean',
    rating_count='count',
    rating_std='std'
).reset_index()
rat_agg.columns = ['movieId', 'avg_rating', 'rating_count', 'rating_std']
rat_agg['rating_std'] = rat_agg['rating_std'].fillna(0)

links = pd.read_csv(os.path.join(PROCESSED, 'train4_small_links_clean.csv'))
links = links[['movieId', 'tmdbId']].dropna()
links['tmdbId'] = links['tmdbId'].astype(int).astype(str)

merged_rat = rat_agg.merge(links, on='movieId', how='left')
merged_rat = merged_rat.rename(columns={'tmdbId': 'id'})
merged_rat['id'] = merged_rat['id'].astype(str)

master = master.merge(
    merged_rat[['id', 'avg_rating', 'rating_count', 'rating_std']],
    on='id', how='left'
)
master['avg_rating']   = master['avg_rating'].fillna(master['vote_average'])
master['rating_count'] = master['rating_count'].fillna(0)
master['rating_std']   = master['rating_std'].fillna(0)

# ── weighted score (already in movies, keep it) ───────────
if 'weighted_score' not in master.columns:
    C = master['vote_average'].mean()
    m = master['vote_count'].quantile(0.70)
    master['weighted_score'] = (
        (master['vote_count'] / (master['vote_count'] + m)) * master['vote_average'] +
        (m / (master['vote_count'] + m)) * C
    )

# ── soup ──────────────────────────────────────────────────
def build_soup(row):
    genres   = ' '.join(row['genre_list'])   if isinstance(row['genre_list'], list)   else ''
    kws      = ' '.join(row['keyword_list']) if isinstance(row['keyword_list'], list) else ''
    cast     = ' '.join(row['cast_list'])    if isinstance(row['cast_list'], list)    else ''
    director = str(row['director'])
    overview = str(row.get('overview', ''))
    return f"{genres} {kws} {cast} {director} {overview}".strip()

master['soup'] = master.apply(build_soup, axis=1)

# ── encode ────────────────────────────────────────────────
le_genre = LabelEncoder()
le_lang  = LabelEncoder()

master['genre_encoded'] = le_genre.fit_transform(
    master['genre_list'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else 'Unknown')
)
master['language_encoded'] = le_lang.fit_transform(
    master['original_language'].fillna('unknown')
)

# ── save ──────────────────────────────────────────────────
keep = [
    'id', 'title', 'overview', 'genres', 'genre_list',
    'original_language', 'popularity', 'year', 'runtime',
    'vote_average', 'vote_count', 'weighted_score',
    'budget', 'revenue',
    'cast_list', 'director', 'keyword_list',
    'avg_rating', 'rating_count', 'rating_std',
    'genre_encoded', 'language_encoded',
    'soup'
]
keep = [c for c in keep if c in master.columns]
master = master[keep].drop_duplicates(subset='id').reset_index(drop=True)

print(f'\nFinal shape : {master.shape}')
print(f'Nulls:\n{master.isnull().sum()}')
print(f'\nSample soup:\n{master["soup"].iloc[0][:300]}')

master.to_csv(MASTER_OUT, index=False)
print(f'\nSaved -> {MASTER_OUT}')
print('STEP 1 COMPLETE')
