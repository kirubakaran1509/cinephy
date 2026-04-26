import ast
import pandas as pd
import numpy as np

def parse_list(x):
    if pd.isna(x) or str(x).strip() in ('', '[]'):
        return []
    try:
        v = ast.literal_eval(str(x))
        if isinstance(v, list):
            return [str(i) for i in v]
    except:
        pass
    return [str(x)]

def safe_float(val, default=0.0):
    try:
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        return float(val) if not pd.isna(val) else default
    except:
        return default

def safe_int(val, default=0):
    try:
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        return int(val) if not pd.isna(val) else default
    except:
        return default

def safe_str(val, default='Unknown'):
    try:
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        s = str(val).strip()
        return s if s not in ('', 'nan', 'None') else default
    except:
        return default

def format_movie_row(row):
    cast   = parse_list(row.get('cast_list', ''))
    genres = parse_list(row.get('genre_list', ''))
    kws    = parse_list(row.get('keyword_list', ''))
    why_parts = []
    if genres:
        why_parts.append('Matching genre: ' + ', '.join(genres[:2]))
    if kws:
        why_parts.append('Similar themes: ' + ', '.join(kws[:3]))
    reason = ' | '.join(why_parts) if why_parts else 'Similar narrative structure and style'
    return {
        'id'      : safe_str(row.get('id', ''), ''),
        'title'   : safe_str(row.get('title', ''), 'Unknown'),
        'year'    : safe_int(row.get('year', 0), 0),
        'genres'  : ', '.join(genres[:3]),
        'director': safe_str(row.get('director', ''), 'Unknown'),
        'cast'    : ', '.join(cast[:5]) if cast else 'N/A',
        'synopsis': safe_str(row.get('overview', ''), ''),
        'reason'  : reason,
        'vote_avg': round(safe_float(row.get('vote_average', 0)), 1),
        'score'   : round(safe_float(row.get('weighted_score', 0)), 2)
    }

def weighted_score(vote_avg, vote_count, C, m):
    return (vote_count / (vote_count + m)) * vote_avg + (m / (vote_count + m)) * C

def paginate(lst, page=1, per_page=10):
    start = (page - 1) * per_page
    end   = start + per_page
    return {
        'data'      : lst[start:end],
        'page'      : page,
        'per_page'  : per_page,
        'total'     : len(lst),
        'pages'     : (len(lst) + per_page - 1) // per_page
    }
