from pymongo import MongoClient, ASCENDING
from config.settings import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db     = client[DB_NAME]

users_col   = db['users']
history_col = db['user_history']
movies_col  = db['movies']

# indexes for fast lookups
history_col.create_index([('user_id', ASCENDING)])
movies_col.create_index([('movieId', ASCENDING)])
