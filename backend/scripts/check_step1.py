import pandas as pd
import numpy as np
import ast
import warnings
warnings.filterwarnings('ignore')

DATA_ROOT = r'C:\Users\kirub\OneDrive\Desktop\MOVIE_DATA'
import os

def safe_parse(obj):
    try:
        return ast.literal_eval(obj)
    except:
        return []

def extract_names(obj, key='name', limit=None):
    items = safe_parse(obj) if isinstance(obj, str) else (obj or [])
    names = [i[key] for i in items if isinstance(i, dict) and key in i]
    return names[:limit] if limit else names

print('Loading movies_metadata...')
df = pd.read_csv(os.path.join(DATA_ROOT, 'data_train_3', 'movies_metadata.csv'), low_memory=False)
print('Raw shape:', df.shape)

# DROP useless columns
drop_cols = [
    'adult', 'belongs_to_collection', 'homepage',
    'poster_path', 'video', 'imdb_id', 'original_title',
    'spoken_languages', 'production_countries', 'tagline'
]
df.drop(columns=drop_cols, inplace=True)
print('After drop:', df.shape)

# Fix id - remove bad rows
df = df[pd.to_numeric(df['id'], errors='coerce').notna()]
df['id'] = df['id'].astype(int).astype(str)

# Fix numeric columns
for col in ['budget','revenue','runtime','popularity','vote_average','vote_count']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Fill nulls
df['budget']     = df['budget'].fillna(0)
df['revenue']    = df['revenue'].fillna(0)
df['runtime']    = df['runtime'].fillna(df['runtime'].median())
df['popularity'] = df['popularity'].fillna(df['popularity'].median())
df['vote_average']= df['vote_average'].fillna(df['vote_average'].mean())
df['vote_count'] = df['vote_count'].fillna(0)

# Keep only Released
df = df[df['status'] == 'Released'].copy()
df.drop(columns=['status'], inplace=True)

# Parse genres
df['genres_list'] = df['genres'].apply(lambda x: extract_names(x))
df['genres_str']  = df['genres_list'].apply(lambda x: '|'.join(x))

# Parse production companies (top 2 only)
df['companies'] = df['production_companies'].apply(lambda x: extract_names(x, limit=2))
df.drop(columns=['production_companies'], inplace=True)

# Release year
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
df['year'] = df['release_date'].dt.year.fillna(0).astype(int)
df.drop(columns=['release_date'], inplace=True)

# One line description
df['one_line'] = df['overview'].apply(
    lambda x: str(x).split('.')[0].strip() + '.' if pd.notna(x) and len(str(x)) > 5 else 'No description.'
)

# Drop rows with no title or overview
df.dropna(subset=['title','overview'], inplace=True)

# Drop movies with fewer than 20 votes
df = df[df['vote_count'] >= 20].copy()

# Weighted rating (IMDB formula)
C = df['vote_average'].mean()
m = df['vote_count'].quantile(0.70)
df['weighted_score'] = (
    (df['vote_count'] / (df['vote_count'] + m)) * df['vote_average'] +
    (m / (df['vote_count'] + m)) * C
)

df.reset_index(drop=True, inplace=True)

print('='*60)
print('AFTER CLEANING:')
print('Shape:', df.shape)
print('Columns:', list(df.columns))
print('Nulls remaining:')
print(df.isnull().sum())
print('Sample weighted_score:', df['weighted_score'].describe())
print('Genre sample:', df['genres_list'].iloc[0])
print('One line sample:', df['one_line'].iloc[0])
print('Year range:', df['year'].min(), '-', df['year'].max())
print('='*60)
print('MOVIES METADATA CLEAN - OK')
