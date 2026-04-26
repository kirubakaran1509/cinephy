import pandas as pd
import numpy as np
import ast
import os
import warnings
warnings.filterwarnings('ignore')

DATA_ROOT = r'C:\Users\kirub\OneDrive\Desktop\MOVIE_DATA'
SAVE_ROOT = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data'

os.makedirs(os.path.join(SAVE_ROOT, 'raw'),       exist_ok=True)
os.makedirs(os.path.join(SAVE_ROOT, 'processed'), exist_ok=True)

def safe_parse(obj):
    try:
        return ast.literal_eval(obj)
    except:
        return []

def extract_names(obj, key='name', limit=None):
    items = safe_parse(obj) if isinstance(obj, str) else (obj or [])
    names = [i[key] for i in items if isinstance(i, dict) and key in i]
    return names[:limit] if limit else names

def get_role(crew_str, job):
    for person in safe_parse(crew_str):
        if isinstance(person, dict) and person.get('job') == job:
            return person.get('name', 'Unknown')
    return 'Unknown'

def save_raw(df, name):
    path = os.path.join(SAVE_ROOT, 'raw', name)
    df.to_csv(path, index=False)
    print(f'  RAW saved: {name} | shape: {df.shape}')

def save_processed(df, name):
    path = os.path.join(SAVE_ROOT, 'processed', name)
    df.to_csv(path, index=False)
    print(f'  PROCESSED saved: {name} | shape: {df.shape}')

# ════════════════════════════════════════════════════
# DATA_TEST_1 — links, movies, ratings, tags
# ════════════════════════════════════════════════════
print('='*55)
print('DATA_TEST_1')
print('='*55)

# links
df = pd.read_csv(os.path.join(DATA_ROOT,'data_test_1','links.csv'))
save_raw(df, 'test1_links_raw.csv')
df.dropna(inplace=True)
df = df.astype(int)
save_processed(df, 'test1_links_clean.csv')

# movies
df = pd.read_csv(os.path.join(DATA_ROOT,'data_test_1','movies.csv'))
save_raw(df, 'test1_movies_raw.csv')
df.dropna(subset=['title'], inplace=True)
df['genres'] = df['genres'].replace('(no genres listed)', np.nan).fillna('Unknown')
save_processed(df, 'test1_movies_clean.csv')

# ratings
df = pd.read_csv(os.path.join(DATA_ROOT,'data_test_1','ratings.csv'))
save_raw(df, 'test1_ratings_raw.csv')
df.drop(columns=['timestamp'], inplace=True)
df.dropna(inplace=True)
df.drop_duplicates(subset=['userId','movieId'], inplace=True)
df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
df.dropna(subset=['rating'], inplace=True)
save_processed(df, 'test1_ratings_clean.csv')

# tags
df = pd.read_csv(os.path.join(DATA_ROOT,'data_test_1','tags.csv'))
save_raw(df, 'test1_tags_raw.csv')
df.drop(columns=['timestamp'], inplace=True)
df.dropna(inplace=True)
df['tag'] = df['tag'].astype(str).str.lower().str.strip()
save_processed(df, 'test1_tags_clean.csv')

# ════════════════════════════════════════════════════
# DATA_TEST_2 — links, movies, ratings, tags
# ════════════════════════════════════════════════════
print('='*55)
print('DATA_TEST_2')
print('='*55)

# links
df = pd.read_csv(os.path.join(DATA_ROOT,'data_test_2','links.csv'))
save_raw(df, 'test2_links_raw.csv')
df.dropna(inplace=True)
df = df.astype(int)
save_processed(df, 'test2_links_clean.csv')

# movies
df = pd.read_csv(os.path.join(DATA_ROOT,'data_test_2','movies.csv'))
save_raw(df, 'test2_movies_raw.csv')
df.dropna(subset=['title'], inplace=True)
df['genres'] = df['genres'].replace('(no genres listed)', np.nan).fillna('Unknown')
save_processed(df, 'test2_movies_clean.csv')

# ratings
df = pd.read_csv(os.path.join(DATA_ROOT,'data_test_2','ratings.csv'))
save_raw(df, 'test2_ratings_raw.csv')
df.drop(columns=['timestamp'], inplace=True)
df.dropna(inplace=True)
df.drop_duplicates(subset=['userId','movieId'], inplace=True)
df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
df.dropna(subset=['rating'], inplace=True)
save_processed(df, 'test2_ratings_clean.csv')

# tags
df = pd.read_csv(os.path.join(DATA_ROOT,'data_test_2','tags.csv'))
save_raw(df, 'test2_tags_raw.csv')
df.drop(columns=['timestamp'], inplace=True)
df.dropna(inplace=True)
df['tag'] = df['tag'].astype(str).str.lower().str.strip()
save_processed(df, 'test2_tags_clean.csv')

# ════════════════════════════════════════════════════
# DATA_TRAIN_1 — genome_scores, genome_tags, movie, rating, tag
# ════════════════════════════════════════════════════
print('='*55)
print('DATA_TRAIN_1')
print('='*55)

# genome_tags
df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_1','genome_tags.csv'))
save_raw(df, 'train1_genome_tags_raw.csv')
df.columns = [c.strip().strip('"') for c in df.columns]
df.dropna(inplace=True)
df['tag'] = df['tag'].astype(str).str.lower().str.strip()
save_processed(df, 'train1_genome_tags_clean.csv')

# genome_scores - large file, sample top relevance only
print('  Loading genome_scores (large)...')
df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_1','genome_scores.csv'))
save_raw(df, 'train1_genome_scores_raw.csv')
df.columns = [c.strip().strip('"') for c in df.columns]
df['relevance'] = pd.to_numeric(df['relevance'], errors='coerce')
df.dropna(inplace=True)
# Keep only high relevance tags (>0.5) to reduce size
df = df[df['relevance'] > 0.5]
save_processed(df, 'train1_genome_scores_clean.csv')

# movie
df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_1','movie.csv'))
save_raw(df, 'train1_movies_raw.csv')
df.columns = [c.strip().strip('"') for c in df.columns]
df.dropna(subset=['title'], inplace=True)
df['genres'] = df['genres'].replace('(no genres listed)', np.nan).fillna('Unknown')
save_processed(df, 'train1_movies_clean.csv')

# rating - large file, load in chunks
print('  Loading train1 ratings (large)...')
chunks = []
for chunk in pd.read_csv(os.path.join(DATA_ROOT,'data_train_1','rating.csv'), chunksize=500000):
    chunk.columns = [c.strip().strip('"') for c in chunk.columns]
    chunk.drop(columns=['timestamp'], inplace=True, errors='ignore')
    chunk.dropna(inplace=True)
    chunk.drop_duplicates(subset=['userId','movieId'], inplace=True)
    chunk['rating'] = pd.to_numeric(chunk['rating'], errors='coerce')
    chunk.dropna(subset=['rating'], inplace=True)
    chunks.append(chunk)
df = pd.concat(chunks, ignore_index=True)
df.drop_duplicates(subset=['userId','movieId'], inplace=True)
save_raw(df, 'train1_ratings_raw.csv')
save_processed(df, 'train1_ratings_clean.csv')

# tag
df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_1','tag.csv'))
save_raw(df, 'train1_tags_raw.csv')
df.columns = [c.strip().strip('"') for c in df.columns]
df.drop(columns=['timestamp'], inplace=True, errors='ignore')
df.dropna(inplace=True)
df['tag'] = df['tag'].astype(str).str.lower().str.strip()
save_processed(df, 'train1_tags_clean.csv')

# ════════════════════════════════════════════════════
# DATA_TRAIN_2 — genome_scores, genome_tags, movies, ratings, tags
# ════════════════════════════════════════════════════
print('='*55)
print('DATA_TRAIN_2')
print('='*55)

# genome_tags
df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_2','genome-tags.csv'))
save_raw(df, 'train2_genome_tags_raw.csv')
df.dropna(inplace=True)
df['tag'] = df['tag'].astype(str).str.lower().str.strip()
save_processed(df, 'train2_genome_tags_clean.csv')

# genome_scores
print('  Loading genome_scores train2 (large)...')
df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_2','genome-scores.csv'))
save_raw(df, 'train2_genome_scores_raw.csv')
df['relevance'] = pd.to_numeric(df['relevance'], errors='coerce')
df.dropna(inplace=True)
df = df[df['relevance'] > 0.5]
save_processed(df, 'train2_genome_scores_clean.csv')

# movies
df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_2','movies.csv'))
save_raw(df, 'train2_movies_raw.csv')
df.dropna(subset=['title'], inplace=True)
df['genres'] = df['genres'].replace('(no genres listed)', np.nan).fillna('Unknown')
save_processed(df, 'train2_movies_clean.csv')

# ratings - large
print('  Loading train2 ratings (large)...')
chunks = []
for chunk in pd.read_csv(os.path.join(DATA_ROOT,'data_train_2','ratings.csv'), chunksize=500000):
    chunk.drop(columns=['timestamp'], inplace=True, errors='ignore')
    chunk.dropna(inplace=True)
    chunk.drop_duplicates(subset=['userId','movieId'], inplace=True)
    chunk['rating'] = pd.to_numeric(chunk['rating'], errors='coerce')
    chunk.dropna(subset=['rating'], inplace=True)
    chunks.append(chunk)
df = pd.concat(chunks, ignore_index=True)
df.drop_duplicates(subset=['userId','movieId'], inplace=True)
save_raw(df, 'train2_ratings_raw.csv')
save_processed(df, 'train2_ratings_clean.csv')

# tags
df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_2','tags.csv'))
save_raw(df, 'train2_tags_raw.csv')
df.drop(columns=['timestamp'], inplace=True, errors='ignore')
df.dropna(inplace=True)
df['tag'] = df['tag'].astype(str).str.lower().str.strip()
save_processed(df, 'train2_tags_clean.csv')

# ════════════════════════════════════════════════════
# DATA_TRAIN_3 — credits, keywords, movies_metadata, ratings, ratings_small
# ════════════════════════════════════════════════════
print('='*55)
print('DATA_TRAIN_3')
print('='*55)

# movies_metadata
df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_3','movies_metadata.csv'), low_memory=False)
save_raw(df, 'train3_movies_metadata_raw.csv')
drop_cols = ['adult','belongs_to_collection','homepage','poster_path',
             'video','imdb_id','original_title','spoken_languages',
             'production_countries','tagline']
df.drop(columns=drop_cols, inplace=True)
df = df[pd.to_numeric(df['id'], errors='coerce').notna()]
df['id'] = df['id'].astype(int).astype(str)
for col in ['budget','revenue','runtime','popularity','vote_average','vote_count']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df['budget']       = df['budget'].fillna(0)
df['revenue']      = df['revenue'].fillna(0)
df['runtime']      = df['runtime'].fillna(df['runtime'].median())
df['popularity']   = df['popularity'].fillna(df['popularity'].median())
df['vote_average'] = df['vote_average'].fillna(df['vote_average'].mean())
df['vote_count']   = df['vote_count'].fillna(0)
df['original_language'] = df['original_language'].fillna('en')
df = df[df['status'] == 'Released'].copy()
df.drop(columns=['status'], inplace=True)
df['genres_list'] = df['genres'].apply(lambda x: extract_names(x))
df['genres_str']  = df['genres_list'].apply(lambda x: '|'.join(x))
df['companies']   = df['production_companies'].apply(lambda x: extract_names(x, limit=2))
df.drop(columns=['production_companies'], inplace=True)
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
df['year']         = df['release_date'].dt.year.fillna(0).astype(int)
df.drop(columns=['release_date'], inplace=True)
df['one_line']     = df['overview'].apply(
    lambda x: str(x).split('.')[0].strip() + '.' if pd.notna(x) and len(str(x)) > 5 else 'No description.'
)
df.dropna(subset=['title','overview'], inplace=True)
df = df[df['vote_count'] >= 20].copy()
C = df['vote_average'].mean()
m = df['vote_count'].quantile(0.70)
df['weighted_score'] = (
    (df['vote_count'] / (df['vote_count'] + m)) * df['vote_average'] +
    (m / (df['vote_count'] + m)) * C
)
df.reset_index(drop=True, inplace=True)
save_processed(df, 'train3_movies_clean.csv')

# credits
cr = pd.read_csv(os.path.join(DATA_ROOT,'data_train_3','credits.csv'))
save_raw(cr, 'train3_credits_raw.csv')
cr['id']         = cr['id'].astype(str)
cr['cast_names'] = cr['cast'].apply(lambda x: extract_names(x, key='name', limit=5))
cr['characters'] = cr['cast'].apply(lambda x: extract_names(x, key='character', limit=3))
cr['director']   = cr['crew'].apply(lambda x: get_role(x, 'Director'))
cr['producer']   = cr['crew'].apply(lambda x: get_role(x, 'Producer'))
cr['writer']     = cr['crew'].apply(lambda x: get_role(x, 'Screenplay'))
cr.drop(columns=['cast','crew'], inplace=True)
save_processed(cr, 'train3_credits_clean.csv')

# keywords
kw = pd.read_csv(os.path.join(DATA_ROOT,'data_train_3','keywords.csv'))
save_raw(kw, 'train3_keywords_raw.csv')
kw['id']            = kw['id'].astype(str)
kw['keywords_list'] = kw['keywords'].apply(lambda x: extract_names(x))
kw.drop(columns=['keywords'], inplace=True)
save_processed(kw, 'train3_keywords_clean.csv')

# ratings_small
rt = pd.read_csv(os.path.join(DATA_ROOT,'data_train_3','ratings_small.csv'))
save_raw(rt, 'train3_ratings_small_raw.csv')
rt.drop(columns=['timestamp'], inplace=True)
rt.dropna(inplace=True)
rt.drop_duplicates(subset=['userId','movieId'], inplace=True)
rt['rating'] = pd.to_numeric(rt['rating'], errors='coerce')
rt.dropna(subset=['rating'], inplace=True)
rt.reset_index(drop=True, inplace=True)
save_processed(rt, 'train3_ratings_small_clean.csv')

# ratings full - large
print('  Loading train3 ratings full (large)...')
chunks = []
for chunk in pd.read_csv(os.path.join(DATA_ROOT,'data_train_3','ratings.csv'), chunksize=500000):
    chunk.drop(columns=['timestamp'], inplace=True, errors='ignore')
    chunk.dropna(inplace=True)
    chunk.drop_duplicates(subset=['userId','movieId'], inplace=True)
    chunk['rating'] = pd.to_numeric(chunk['rating'], errors='coerce')
    chunk.dropna(subset=['rating'], inplace=True)
    chunks.append(chunk)
df = pd.concat(chunks, ignore_index=True)
df.drop_duplicates(subset=['userId','movieId'], inplace=True)
save_raw(df, 'train3_ratings_full_raw.csv')
save_processed(df, 'train3_ratings_full_clean.csv')

# ════════════════════════════════════════════════════
# DATA_TRAIN_4 — movies_metadata + ml-latest-small
# ════════════════════════════════════════════════════
print('='*55)
print('DATA_TRAIN_4')
print('='*55)

# movies_metadata (same as train3, just copy processed)
df = pd.read_csv(os.path.join(SAVE_ROOT,'processed','train3_movies_clean.csv'))
save_processed(df, 'train4_movies_clean.csv')
print('  train4 movies reused from train3')

# ml-latest-small
for fname in ['links','movies','ratings','tags']:
    df = pd.read_csv(os.path.join(DATA_ROOT,'data_train_4','ml-latest-small', fname+'.csv'))
    save_raw(df, f'train4_small_{fname}_raw.csv')
    if 'timestamp' in df.columns:
        df.drop(columns=['timestamp'], inplace=True)
    if fname == 'ratings':
        df.dropna(inplace=True)
        df.drop_duplicates(subset=['userId','movieId'], inplace=True)
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        df.dropna(subset=['rating'], inplace=True)
    if fname == 'movies':
        df['genres'] = df['genres'].replace('(no genres listed)', np.nan).fillna('Unknown')
    if fname == 'tags':
        df['tag'] = df['tag'].astype(str).str.lower().str.strip()
    df.reset_index(drop=True, inplace=True)
    save_processed(df, f'train4_small_{fname}_clean.csv')

# ════════════════════════════════════════════════════
# DATA_TRAIN_5 — tmdb_5000_movies + tmdb_5000_credits
# ════════════════════════════════════════════════════
print('='*55)
print('DATA_TRAIN_5')
print('='*55)

# tmdb movies
tm = pd.read_csv(os.path.join(DATA_ROOT,'data_train_5','tmdb_5000_movies.csv'))
save_raw(tm, 'train5_tmdb_movies_raw.csv')
tm.drop(columns=['homepage','original_title','spoken_languages',
                 'production_countries','tagline'], inplace=True)
tm['keywords_list'] = tm['keywords'].apply(lambda x: extract_names(x))
tm['genres_list']   = tm['genres'].apply(lambda x: extract_names(x))
tm['companies']     = tm['production_companies'].apply(lambda x: extract_names(x, limit=2))
tm.drop(columns=['keywords','genres','production_companies'], inplace=True)
tm['release_date']  = pd.to_datetime(tm['release_date'], errors='coerce')
tm['year']          = tm['release_date'].dt.year.fillna(0).astype(int)
tm.drop(columns=['release_date'], inplace=True)
tm['overview']      = tm['overview'].fillna('No description.')
tm['runtime']       = pd.to_numeric(tm['runtime'], errors='coerce').fillna(tm['runtime'].median())
tm['budget']        = pd.to_numeric(tm['budget'], errors='coerce').fillna(0)
tm['revenue']       = pd.to_numeric(tm['revenue'], errors='coerce').fillna(0)
tm.reset_index(drop=True, inplace=True)
save_processed(tm, 'train5_tmdb_movies_clean.csv')

# tmdb credits
tc = pd.read_csv(os.path.join(DATA_ROOT,'data_train_5','tmdb_5000_credits.csv'))
save_raw(tc, 'train5_tmdb_credits_raw.csv')
tc.rename(columns={'movie_id':'id'}, inplace=True)
tc['id']         = tc['id'].astype(str)
tc['cast_names'] = tc['cast'].apply(lambda x: extract_names(x, key='name', limit=5))
tc['characters'] = tc['cast'].apply(lambda x: extract_names(x, key='character', limit=3))
tc['director']   = tc['crew'].apply(lambda x: get_role(x, 'Director'))
tc['producer']   = tc['crew'].apply(lambda x: get_role(x, 'Producer'))
tc['writer']     = tc['crew'].apply(lambda x: get_role(x, 'Screenplay'))
tc.drop(columns=['cast','crew','title'], inplace=True)
save_processed(tc, 'train5_tmdb_credits_clean.csv')

# ════════════════════════════════════════════════════
# DATA_TRAIN_7 — imdb_top_1000
# ════════════════════════════════════════════════════
print('='*55)
print('DATA_TRAIN_7')
print('='*55)

imdb = pd.read_csv(os.path.join(DATA_ROOT,'data_train_7','imdb_top_1000.csv'))
save_raw(imdb, 'train7_imdb_raw.csv')
imdb.drop(columns=['Poster_Link','Certificate','Gross'], inplace=True)
imdb.rename(columns={
    'Series_Title':  'title',
    'Released_Year': 'imdb_year',
    'Runtime':       'imdb_runtime',
    'Genre':         'imdb_genre',
    'IMDB_Rating':   'imdb_rating',
    'Overview':      'imdb_overview',
    'Meta_score':    'meta_score',
    'Director':      'imdb_director',
    'Star1':'star1','Star2':'star2','Star3':'star3','Star4':'star4',
    'No_of_Votes':   'imdb_votes'
}, inplace=True)
imdb['meta_score']   = pd.to_numeric(imdb['meta_score'],  errors='coerce')
imdb['meta_score']   = imdb['meta_score'].fillna(imdb['meta_score'].median())
imdb['imdb_votes']   = pd.to_numeric(imdb['imdb_votes'].astype(str).str.replace(',',''), errors='coerce').fillna(0)
imdb['imdb_rating']  = pd.to_numeric(imdb['imdb_rating'], errors='coerce').fillna(0)
imdb['imdb_runtime'] = imdb['imdb_runtime'].astype(str).str.replace(' min','').str.strip()
imdb['imdb_runtime'] = pd.to_numeric(imdb['imdb_runtime'], errors='coerce').fillna(0)
imdb.reset_index(drop=True, inplace=True)
save_processed(imdb, 'train7_imdb_clean.csv')

# ════════════════════════════════════════════════════
# DATA_TRAIN_8 — anime (reference only, not merged)
# ════════════════════════════════════════════════════
print('='*55)
print('DATA_TRAIN_8 (anime - saved as reference)')
print('='*55)

anime = pd.read_csv(os.path.join(DATA_ROOT,'data_train_8','anime.csv'))
save_raw(anime, 'train8_anime_raw.csv')
anime.dropna(subset=['name'], inplace=True)
anime['rating']  = pd.to_numeric(anime['rating'],  errors='coerce').fillna(0)
anime['members'] = pd.to_numeric(anime['members'], errors='coerce').fillna(0)
anime['episodes']= pd.to_numeric(anime['episodes'].replace('Unknown', np.nan), errors='coerce').fillna(0)
save_processed(anime, 'train8_anime_clean.csv')

an_rt = pd.read_csv(os.path.join(DATA_ROOT,'data_train_8','rating.csv'))
save_raw(an_rt, 'train8_anime_ratings_raw.csv')
an_rt = an_rt[an_rt['rating'] != -1]
an_rt.dropna(inplace=True)
an_rt.drop_duplicates(subset=['user_id','anime_id'], inplace=True)
save_processed(an_rt, 'train8_anime_ratings_clean.csv')

# ════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════
print()
print('='*55)
print('ALL FILES SAVED')
print('='*55)
print('\nRAW FILES:')
raw_files = os.listdir(os.path.join(SAVE_ROOT,'raw'))
for f in sorted(raw_files):
    size = os.path.getsize(os.path.join(SAVE_ROOT,'raw',f))
    print(f'  {f:50s} {size/1024:>8.1f} KB')

print('\nPROCESSED FILES:')
pro_files = os.listdir(os.path.join(SAVE_ROOT,'processed'))
for f in sorted(pro_files):
    size = os.path.getsize(os.path.join(SAVE_ROOT,'processed',f))
    print(f'  {f:50s} {size/1024:>8.1f} KB')

print('\nDONE!')
