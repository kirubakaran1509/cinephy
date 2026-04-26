import pandas as pd
import ast
import os

MASTER_OUT = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed\master_movies.csv'
PROCESSED  = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed'

print('Fixing cast_list from source...')
df       = pd.read_csv(MASTER_OUT)
credits  = pd.read_csv(os.path.join(PROCESSED, 'train3_credits_clean.csv'))

# cast_names looks like: ['Tom Hanks', 'Tim Allen', 'Don Rickles']
# ast.literal_eval handles this perfectly
def parse_cast(x):
    if pd.isna(x) or str(x).strip() == '':
        return []
    try:
        lst = ast.literal_eval(str(x))
        if isinstance(lst, list):
            return [str(n).strip() for n in lst[:5] if str(n).strip()]
    except:
        pass
    return []

credits['cast_list'] = credits['cast_names'].apply(parse_cast)
credits['id']        = credits['id'].astype(str)

print('Sample cast_list from credits:')
print(credits['cast_list'].head(3).tolist())

# drop old cast_list and re-merge
df['id'] = df['id'].astype(str)
df = df.drop(columns=['cast_list'])
df = df.merge(credits[['id','cast_list']], on='id', how='left')
df['cast_list'] = df['cast_list'].apply(lambda x: x if isinstance(x, list) else [])

# rebuild soup cleanly
def safe_list(x):
    if isinstance(x, list): return x
    try:    return ast.literal_eval(x)
    except: return []

def build_soup(row):
    genres   = ' '.join(safe_list(row['genre_list']))
    kws      = ' '.join(safe_list(row['keyword_list']))
    cast     = ' '.join(row['cast_list'])
    director = str(row['director'])
    overview = str(row.get('overview',''))
    return f"{genres} {kws} {cast} {director} {overview}".strip()

df['soup'] = df.apply(build_soup, axis=1)

print('\nSample cast_list in master:')
print(df['cast_list'].head(3).tolist())
print('\nSample soup:')
print(df['soup'].iloc[0][:300])
print('\nNulls:')
print(df[['cast_list','director','soup']].isnull().sum())

df.to_csv(MASTER_OUT, index=False)
print(f'\nSaved -> {MASTER_OUT}')
print('FIX COMPLETE')
