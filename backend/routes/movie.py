from flask import Blueprint, jsonify, request
from ml_engine import master
import ast
import pandas as pd

movie_bp = Blueprint('movie', __name__)

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

@movie_bp.route('/movie/<string:movie_id>', methods=['GET'])
def get_movie(movie_id):
    subset = master[master['id'].astype(str) == str(movie_id)]
    if subset.empty:
        return jsonify({'error': 'Movie not found'}), 404
    row    = subset.iloc[0]
    cast   = parse_list(row.get('cast_list', ''))
    genres = parse_list(row.get('genre_list', ''))
    kws    = parse_list(row.get('keyword_list', ''))
    yr     = int(row['year']) if not pd.isna(row.get('year', 0)) else 0
    return jsonify({
        'id'        : str(row['id']),
        'title'     : str(row['title']),
        'year'      : yr,
        'genres'    : genres,
        'director'  : str(row.get('director', 'Unknown')),
        'cast'      : cast[:5],
        'keywords'  : kws[:10],
        'synopsis'  : str(row.get('overview', '')),
        'vote_avg'  : round(float(row['vote_average']), 1),
        'vote_count': int(row.get('vote_count', 0)),
        'score'     : round(float(row['weighted_score']), 2),
        'popularity': round(float(row.get('popularity', 0)), 2),
        'runtime'   : int(row.get('runtime', 0)) if not pd.isna(row.get('runtime', 0)) else 0,
        'language'  : str(row.get('original_language', 'en')),
        'budget'    : int(row.get('budget', 0)) if not pd.isna(row.get('budget', 0)) else 0,
        'revenue'   : int(row.get('revenue', 0)) if not pd.isna(row.get('revenue', 0)) else 0
    })

@movie_bp.route('/movies/search', methods=['GET'])
def search_movies():
    query = request.args.get('q', '').lower().strip()
    if not query or len(query) < 2:
        return jsonify({'error': 'Query too short'}), 400
    matches = master[master['title'].str.lower().str.contains(query, na=False)].head(10)
    if matches.empty:
        return jsonify({'results': []})
    results = []
    for _, row in matches.iterrows():
        genres = parse_list(row.get('genre_list', ''))
        yr     = int(row['year']) if not pd.isna(row.get('year', 0)) else 0
        results.append({
            'id'      : str(row['id']),
            'title'   : str(row['title']),
            'year'    : yr,
            'genres'  : ', '.join(genres[:3]),
            'vote_avg': round(float(row['vote_average']), 1),
            'score'   : round(float(row['weighted_score']), 2)
        })
    return jsonify({'results': results})

@movie_bp.route('/movies/top', methods=['GET'])
def top_movies():
    n      = int(request.args.get('n', 10))
    genre  = request.args.get('genre', '').strip().lower()
    if genre:
        filtered = master[master['genre_list'].str.lower().str.contains(genre, na=False)]
    else:
        filtered = master.copy()
    top = filtered.nlargest(n, 'weighted_score')
    results = []
    for _, row in top.iterrows():
        genres = parse_list(row.get('genre_list', ''))
        yr     = int(row['year']) if not pd.isna(row.get('year', 0)) else 0
        results.append({
            'id'      : str(row['id']),
            'title'   : str(row['title']),
            'year'    : yr,
            'genres'  : ', '.join(genres[:3]),
            'director': str(row.get('director', 'Unknown')),
            'synopsis': str(row.get('overview', '')),
            'vote_avg': round(float(row['vote_average']), 1),
            'score'   : round(float(row['weighted_score']), 2)
        })
    return jsonify({'results': results})
