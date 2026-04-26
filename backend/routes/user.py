from flask import Blueprint, request, jsonify
from config.db import history_col, users_col
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/history', methods=['POST'])
def save_history():
    data     = request.get_json()
    user_id  = data.get('user_id')
    movie_id = data.get('movie_id')
    title    = data.get('title', '')
    rating   = data.get('rating', None)
    if not user_id or not movie_id:
        return jsonify({'error': 'user_id and movie_id are required'}), 400
    record = {
        'user_id'   : user_id,
        'movie_id'  : str(movie_id),
        'title'     : title,
        'rating'    : rating,
        'watched_at': datetime.utcnow().isoformat()
    }
    history_col.insert_one(record)
    set_op = '$' + 'set'
    inc_op = '$' + 'inc'
    users_col.update_one(
        {'user_id': user_id},
        {set_op: {'user_id': user_id, 'last_active': datetime.utcnow().isoformat()},
         inc_op: {'total_watched': 1}},
        upsert=True
    )
    return jsonify({'status': 'saved', 'record': {k: v for k, v in record.items() if k != '_id'}})

@user_bp.route('/user/history/<string:user_id>', methods=['GET'])
def get_history(user_id):
    limit   = int(request.args.get('limit', 20))
    records = list(history_col.find(
        {'user_id': user_id},
        {'_id': 0}
    ).sort('watched_at', -1).limit(limit))
    return jsonify({'user_id': user_id, 'history': records, 'count': len(records)})

@user_bp.route('/user/history/<string:user_id>', methods=['DELETE'])
def delete_history(user_id):
    result = history_col.delete_many({'user_id': user_id})
    return jsonify({'status': 'deleted', 'deleted_count': result.deleted_count})

@user_bp.route('/user/rate', methods=['POST'])
def rate_movie():
    data     = request.get_json()
    user_id  = data.get('user_id')
    movie_id = data.get('movie_id')
    rating   = data.get('rating')
    if not user_id or not movie_id or rating is None:
        return jsonify({'error': 'user_id, movie_id and rating are required'}), 400
    if not (0.5 <= float(rating) <= 5.0):
        return jsonify({'error': 'Rating must be between 0.5 and 5.0'}), 400
    set_op = '$' + 'set'
    history_col.update_one(
        {'user_id': user_id, 'movie_id': str(movie_id)},
        {set_op: {'rating': float(rating), 'rated_at': datetime.utcnow().isoformat()}},
        upsert=True
    )
    return jsonify({'status': 'rated', 'user_id': user_id, 'movie_id': movie_id, 'rating': rating})

@user_bp.route('/user/<string:user_id>', methods=['GET'])
def get_user(user_id):
    user = users_col.find_one({'user_id': user_id}, {'_id': 0})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user)
