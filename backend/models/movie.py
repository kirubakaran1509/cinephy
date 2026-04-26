from config.db import movies_col
from datetime import datetime

def upsert_movie(movie_data):
    set_op = '$' + 'set'
    movies_col.update_one(
        {'movieId': movie_data['movieId']},
        {set_op: movie_data},
        upsert=True
    )

def get_movie_by_id(movie_id):
    return movies_col.find_one({'movieId': str(movie_id)}, {'_id': 0})

def get_top_movies(n=10, genre=None):
    query = {}
    if genre:
        query['genres'] = {'$' + 'regex': genre, '$' + 'options': 'i'}
    return list(movies_col.find(query, {'_id': 0}).sort('score', -1).limit(n))

def search_movies(query_str, limit=10):
    regex_op  = '$' + 'regex'
    option_op = '$' + 'options'
    return list(movies_col.find(
        {'title': {regex_op: query_str, option_op: 'i'}},
        {'_id': 0}
    ).limit(limit))
