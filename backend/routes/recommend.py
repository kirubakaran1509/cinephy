from flask import Blueprint, request, jsonify
from ml_engine import master, indices, tfidf_m, content_cache, ens_cache, mid_to_tmdb
from sklearn.metrics.pairwise import cosine_similarity as cos_sim
import numpy as np
import ast
import pandas as pd

recommend_bp = Blueprint('recommend', __name__)

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

def get_recs_by_title(title, n=5):
    key = title.lower().strip()
    if key not in indices:
        return None, []
    idx  = indices[key]
    sims = cos_sim(tfidf_m[idx], tfidf_m).flatten()

    # Get top 100 candidates, filter out low quality, then rerank
    top_idx = np.argsort(sims)[::-1][1:101]

    candidates = []
    for i in top_idx:
        row     = master.iloc[i]
        mid_str = str(row['id'])
        sim     = float(sims[i])
        ws      = float(row.get('weighted_score', 5.5))
        ens     = float(ens_cache.get(mid_str, 5.5))
        vote_c  = float(row.get('vote_count', 0))

        # Skip low quality movies
        if ws < 6.5 or vote_c < 100:
            continue

        # Blend: 50% content sim (scaled 0-10) + 30% weighted_score + 20% ensemble
        blended = (sim * 10 * 0.50) + (ws * 0.30) + (ens * 0.20)
        candidates.append((i, blended))

    # Sort by blended score, take top n
    candidates.sort(key=lambda x: x[1], reverse=True)
    top_n = candidates[:n]

    results = []
    for i, blended in top_n:
        row     = master.iloc[i]
        cast    = parse_list(row.get('cast_list', ''))
        kws     = parse_list(row.get('keyword_list', ''))
        genres  = parse_list(row.get('genre_list', ''))
        why_parts = []
        if genres:
            why_parts.append('Matching genre: ' + ', '.join(genres[:2]))
        if kws:
            why_parts.append('Similar themes: ' + ', '.join(kws[:3]))
        why = ' | '.join(why_parts) if why_parts else 'Similar narrative structure and style'
        yr  = int(row['year']) if not pd.isna(row.get('year', 0)) else 0
        results.append({
            'rank'    : len(results) + 1,
            'title'   : str(row['title']),
            'year'    : yr,
            'genres'  : ', '.join(genres[:3]),
            'director': str(row.get('director', 'Unknown')),
            'cast'    : ', '.join(cast[:5]) if cast else 'N/A',
            'synopsis': str(row.get('overview', '')),
            'reason'  : why,
            'vote_avg': round(float(row['vote_average']), 1),
            'score'   : round(float(row['weighted_score']), 2)
        })
    return str(master.iloc[idx]['title']), results

def get_recs_by_user(user_id, n=5):
    scores = {}
    for mid_str in list(content_cache.keys()):
        try:
            mid_int = int(mid_str)
            from app import get_svd; svd_s = get_svd().predict(user_id, mid_int) * 2.0
            scores[mid_str] = (0.40 * content_cache.get(mid_str, 5.5) +
                               0.35 * svd_s +
                               0.25 * ens_cache.get(mid_str, 5.5))
        except:
            continue
    top_ids = sorted(scores, key=scores.get, reverse=True)[:n]
    results = []
    for mid_str in top_ids:
        subset = master[master['id'].astype(str) == mid_str]
        if subset.empty:
            continue
        row    = subset.iloc[0]
        cast   = parse_list(row.get('cast_list', ''))
        genres = parse_list(row.get('genre_list', ''))
        kws    = parse_list(row.get('keyword_list', ''))
        why_parts = []
        if genres:
            why_parts.append('Matching genre: ' + ', '.join(genres[:2]))
        if kws:
            why_parts.append('Similar themes: ' + ', '.join(kws[:3]))
        why = ' | '.join(why_parts) if why_parts else 'Recommended based on your taste'
        yr  = int(row['year']) if not pd.isna(row.get('year', 0)) else 0
        results.append({
            'rank'    : len(results) + 1,
            'title'   : str(row['title']),
            'year'    : yr,
            'genres'  : ', '.join(genres[:3]),
            'director': str(row.get('director', 'Unknown')),
            'cast'    : ', '.join(cast[:5]) if cast else 'N/A',
            'synopsis': str(row.get('overview', '')),
            'reason'  : why,
            'vote_avg': round(float(row['vote_average']), 1),
            'score'   : round(float(row['weighted_score']), 2)
        })
    return results

@recommend_bp.route('/recommend', methods=['POST'])
def recommend():
    data    = request.get_json()
    title   = data.get('title', '').strip()
    user_id = data.get('user_id', None)
    n       = int(data.get('n', 5))
    if title:
        matched_title, recs = get_recs_by_title(title, n)
        if not recs:
            return jsonify({'error': 'Movie not found: ' + title}), 404
        return jsonify({
            'type'           : 'content',
            'input_title'    : matched_title,
            'recommendations': recs
        })
    elif user_id:
        recs = get_recs_by_user(user_id, n)
        if not recs:
            return jsonify({'error': 'No recommendations found for user'}), 404
        return jsonify({
            'type'           : 'collaborative',
            'user_id'        : user_id,
            'recommendations': recs
        })
    else:
        return jsonify({'error': 'Provide title or user_id'}), 400
