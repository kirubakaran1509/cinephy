import warnings; warnings.filterwarnings('ignore')
import os, pickle, ast
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import scipy.sparse as sp

PROC  = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed'
SAVED = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\ml\saved_models'

master = pd.read_csv(os.path.join(PROC, 'master_movies.csv'))

def parse_list(x):
    if pd.isna(x) or str(x).strip() in ('','[]'): return []
    try:
        v = ast.literal_eval(str(x))
        if isinstance(v, list): return [str(i) for i in v]
    except: pass
    return [str(x)]

def build_soup(row):
    genres   = ' '.join(parse_list(row.get('genre_list','')))
    keywords = ' '.join(parse_list(row.get('keyword_list','')))
    cast     = ' '.join(parse_list(row.get('cast_list',''))[:3])
    director = str(row.get('director',''))
    overview = str(row.get('overview',''))
    return (genres+' ')*4 + (keywords+' ')*3 + (director+' ')*3 + (cast+' ')*1 + overview

master['soup'] = master.apply(build_soup, axis=1)
indices = pd.Series(master.index, index=master['title'].str.lower().str.strip())
indices = indices[~indices.index.duplicated(keep='first')]

tfidf = TfidfVectorizer(max_features=15000, ngram_range=(1,2), min_df=2)
matrix = tfidf.fit_transform(master['soup'])

pickle.dump(tfidf,    open(os.path.join(SAVED,'tfidf_vectorizer.pkl'),'wb'))
pickle.dump(dict(indices), open(os.path.join(SAVED,'content_indices.pkl'),'wb'))
sp.save_npz(os.path.join(SAVED,'tfidf_matrix.npz'), matrix.astype(np.float32))
print('Content model rebuilt. Matrix shape:', matrix.shape)
