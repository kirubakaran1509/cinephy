import ast
import warnings
import pandas as pd
import numpy as np
from config.settings import (
    MOVIES_META, CREDITS_3, KEYWORDS_3,
    TMDB_MOVIES, TMDB_CREDITS, IMDB_TOP,
    RATINGS_TRAIN1, RATINGS_TRAIN2, RATINGS_TRAIN3,
    MIN_VOTES
)

warnings.filterwarnings('ignore')

def safe_parse(obj):
    try:
        return ast.literal_eval(obj)
    except Exception:
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

def clean_movies_metadata():
    df = pd.read_csv(MOVIES_META, low_memory=False)

    # DROP columns with no recommendation value
    drop_cols = [
        'adult', 'homepage', 'poster_path', 'video',
        'belongs_to_collection', 'production_countries',
        'spoken_languages', 'imdb_id', 'original_title'
    ]
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    # Fix id column
    df = df[pd.to_numeric(df['id'], errors='coerce').notna()]
    df['id'] = df['id'].astype(int).astype(str)

    # Fix numeric columns
    df['budget']       = pd.to_numeric(df['budget'],       errors='coerce').fillna(0)
    df['revenue']      = pd.to_numeric(df['revenue'],      errors='coerce').fillna(0)
    df['runtime']      = pd.to_numeric(df['runtime'],      errors='coerce').fillna(0)
    df['popularity']   = pd.to_numeric(df['popularity'],   errors='coerce').fillna(0)
    df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0)
    df['vote_count']   = pd.to_numeric(df['vote_count'],   errors='coerce').fillna(0)

    # Parse list columns
    df['genres_list']   = df['genres'].apply(lambda x: extract_names(x))
    df['genres']        = df['genres_list'].apply(lambda x: '|'.join(x))

    df['companies']     = df['production_companies'].apply(lambda x: extract_names(x, limit=3))
    df.drop(columns=['production_companies'], inplace=True)

    # Release year
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['year']         = df['release_date'].dt.year.fillna(0).astype(int)
    df.drop(columns=['release_date'], inplace=True)

    # Status — keep only Released
    df = df[df['status'] == 'Released'].copy()
    df.drop(columns=['status'], inplace=True)

    # One-line description
    df['one_line'] = df['overview'].apply(
        lambda x: str(x).split('.')[0].strip() + '.' if isinstance(x, str) and len(str(x)) > 5 else 'No description.'
    )

    # Filter low vote movies
    df = df[df['vote_count'] >= MIN_VOTES].copy()

    # Drop remaining nulls in key cols
    df.dropna(subset=['title', 'overview'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df

def clean_credits():
    cr = pd.read_csv(CREDITS_3)
    cr['id'] = cr['id'].astype(str)
    cr['cast_names'] = cr['cast'].apply(lambda x: extract_names(x, limit=5))
    cr['director']   = cr['crew'].apply(lambda x: get_role(x, 'Director'))
    cr['producer']   = cr['crew'].apply(lambda x: get_role(x, 'Producer'))
    cr['writer']     = cr['crew'].apply(lambda x: get_role(x, 'Screenplay'))
    cr.drop(columns=['cast', 'crew'], inplace=True)
    return cr

def clean_keywords():
    kw = pd.read_csv(KEYWORDS_3)
    kw['id'] = kw['id'].astype(str)
    kw['keywords_list'] = kw['keywords'].apply(lambda x: extract_names(x))
    kw.drop(columns=['keywords'], inplace=True)
    return kw

def clean_imdb():
    imdb = pd.read_csv(IMDB_TOP)
    imdb.rename(columns={
        'Series_Title': 'title',
        'IMDB_Rating':  'imdb_rating',
        'Meta_score':   'meta_score',
        'Director':     'imdb_director',
        'Star1':        'star1',
        'Star2':        'star2',
        'Star3':        'star3',
        'Star4':        'star4',
        'No_of_Votes':  'imdb_votes',
        'Gross':        'gross',
        'Overview':     'imdb_overview',
        'Genre':        'imdb_genre',
        'Released_Year':'imdb_year',
        'Runtime':      'imdb_runtime',
        'Certificate':  'certificate'
    }, inplace=True)
    # DROP poster link - not useful
    imdb.drop(columns=['Poster_Link'], inplace=True, errors='ignore')
    imdb['imdb_votes'] = pd.to_numeric(
        imdb['imdb_votes'].astype(str).str.replace(',', ''), errors='coerce'
    ).fillna(0)
    imdb['meta_score'] = pd.to_numeric(imdb['meta_score'], errors='coerce').fillna(0)
    return imdb

def load_ratings():
    dfs = []
    for path in [RATINGS_TRAIN1, RATINGS_TRAIN2, RATINGS_TRAIN3]:
        try:
            r = pd.read_csv(path)
            r.columns = [c.lower().strip().strip('\"') for c in r.columns]
            # drop timestamp - not needed
            r.drop(columns=['timestamp'], inplace=True, errors='ignore')
            r.rename(columns={'userid': 'userId', 'movieid': 'movieId'}, inplace=True)
            r = r[['userId', 'movieId', 'rating']].dropna()
            r['rating'] = pd.to_numeric(r['rating'], errors='coerce')
            r.dropna(subset=['rating'], inplace=True)
            dfs.append(r)
        except Exception as e:
            print(f'Skipping {path}: {e}')

    ratings = pd.concat(dfs, ignore_index=True)
    ratings.drop_duplicates(subset=['userId', 'movieId'], inplace=True)
    ratings.reset_index(drop=True, inplace=True)
    return ratings

def build_movies_df():
    print('Loading movies metadata...')
    movies = clean_movies_metadata()

    print('Loading credits...')
    credits = clean_credits()

    print('Loading keywords...')
    keywords = clean_keywords()

    print('Merging...')
    df = movies.merge(credits,  on='id', how='left')
    df = df.merge(keywords, on='id', how='left')

    # Fill nulls after merge
    df['cast_names']    = df['cast_names'].apply(lambda x: x if isinstance(x, list) else [])
    df['keywords_list'] = df['keywords_list'].apply(lambda x: x if isinstance(x, list) else [])
    df['director']      = df['director'].fillna('Unknown')
    df['producer']      = df['producer'].fillna('Unknown')
    df['writer']        = df['writer'].fillna('Unknown')

    # Weighted rating score (IMDB formula)
    C = df['vote_average'].mean()
    m = df['vote_count'].quantile(0.70)
    df['weighted_score'] = (
        (df['vote_count'] / (df['vote_count'] + m)) * df['vote_average'] +
        (m / (df['vote_count'] + m)) * C
    )

    # Content soup for vectorizer
    df['soup'] = (
        df['genres_list'].apply(lambda x: ' '.join(x)) + ' ' +
        df['keywords_list'].apply(lambda x: ' '.join(x[:10])) + ' ' +
        df['cast_names'].apply(lambda x: ' '.join(x)) + ' ' +
        df['director'] + ' ' +
        df['overview'].fillna('')
    )

    print(f'Final movies dataset: {df.shape[0]} rows, {df.shape[1]} columns')
    return df

def load_all():
    movies_df  = build_movies_df()
    ratings_df = load_ratings()
    print(f'Ratings dataset: {ratings_df.shape[0]} rows')
    return movies_df, ratings_df
