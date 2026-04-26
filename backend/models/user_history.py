from config.db import history_col, users_col
from datetime import datetime

def save_watch(user_id, movie_id, title, rating=None):
    set_op = '$' + 'set'
    inc_op = '$' + 'inc'
    record = {
        'user_id'   : user_id,
        'movie_id'  : str(movie_id),
        'title'     : title,
        'rating'    : rating,
        'watched_at': datetime.utcnow().isoformat()
    }
    history_col.insert_one(record)
    users_col.update_one(
        {'user_id': user_id},
        {set_op: {'user_id': user_id, 'last_active': datetime.utcnow().isoformat()},
         inc_op: {'total_watched': 1}},
        upsert=True
    )
    return {k: v for k, v in record.items() if k != '_id'}

def get_user_history(user_id, limit=20):
    return list(history_col.find(
        {'user_id': user_id},
        {'_id': 0}
    ).sort('watched_at', -1).limit(limit))

def get_rated_movies(user_id):
    return list(history_col.find(
        {'user_id': user_id, 'rating': {'$' + 'ne': None}},
        {'_id': 0}
    ).sort('rated_at', -1))

def update_rating(user_id, movie_id, rating):
    set_op = '$' + 'set'
    history_col.update_one(
        {'user_id': user_id, 'movie_id': str(movie_id)},
        {set_op: {'rating': float(rating), 'rated_at': datetime.utcnow().isoformat()}},
        upsert=True
    )

def delete_user_history(user_id):
    result = history_col.delete_many({'user_id': user_id})
    return result.deleted_count

def get_user_stats(user_id):
    user = users_col.find_one({'user_id': user_id}, {'_id': 0})
    if not user:
        return None
    total_rated = history_col.count_documents(
        {'user_id': user_id, 'rating': {'$' + 'ne': None}}
    )
    user['total_rated'] = total_rated
    return user
