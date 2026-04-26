import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME   = os.getenv('DB_NAME', 'movie_recommendation')

DATA_ROOT = os.getenv('DATA_PATH', r'C:\Users\kirub\OneDrive\Desktop\MOVIE_DATA')

# Core content files
MOVIES_META   = os.path.join(DATA_ROOT, 'data_train_3',  'movies_metadata.csv')
CREDITS_3     = os.path.join(DATA_ROOT, 'data_train_3',  'credits.csv')
KEYWORDS_3    = os.path.join(DATA_ROOT, 'data_train_3',  'keywords.csv')

TMDB_MOVIES   = os.path.join(DATA_ROOT, 'data_train_5',  'tmdb_5000_movies.csv')
TMDB_CREDITS  = os.path.join(DATA_ROOT, 'data_train_5',  'tmdb_5000_credits.csv')

IMDB_TOP      = os.path.join(DATA_ROOT, 'data_train_7',  'imdb_top_1000.csv')

# Rating files
RATINGS_TRAIN1 = os.path.join(DATA_ROOT, 'data_train_1', 'rating.csv')
RATINGS_TRAIN2 = os.path.join(DATA_ROOT, 'data_train_2', 'ratings.csv')
RATINGS_TRAIN3 = os.path.join(DATA_ROOT, 'data_train_3', 'ratings_small.csv')
RATINGS_TEST1  = os.path.join(DATA_ROOT, 'data_test_1',  'ratings.csv')
RATINGS_TEST2  = os.path.join(DATA_ROOT, 'data_test_2',  'ratings.csv')

# Genome tag files
GENOME_SCORES = os.path.join(DATA_ROOT, 'data_train_1', 'genome_scores.csv')
GENOME_TAGS   = os.path.join(DATA_ROOT, 'data_train_1', 'genome_tags.csv')

# Recommendation config
TOP_N              = 4
MIN_VOTES          = 50
CONTENT_WEIGHT     = 0.40
COLLAB_WEIGHT      = 0.35
ENSEMBLE_ML_WEIGHT = 0.25
