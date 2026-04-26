import pandas as pd
import os

PROCESSED = r"C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed"

print("="*70)
print("COMPLETE FEATURE AUDIT ACROSS ALL DATASETS")
print("="*70)

files_to_check = {
    "master_movies"        : "master_movies.csv",
    "train3_movies"        : "train3_movies_clean.csv",
    "train3_credits"       : "train3_credits_clean.csv",
    "train3_keywords"      : "train3_keywords_clean.csv",
    "train1_movies"        : "train1_movies_clean.csv",
    "train2_movies"        : "train2_movies_clean.csv",
    "train4_movies"        : "train4_movies_clean.csv",
    "train5_tmdb_movies"   : "train5_tmdb_movies_clean.csv",
    "train5_tmdb_credits"  : "train5_tmdb_credits_clean.csv",
    "train7_imdb"          : "train7_imdb_clean.csv",
    "train1_genome_scores" : "train1_genome_scores_clean.csv",
    "train2_genome_scores" : "train2_genome_scores_clean.csv",
    "train1_genome_tags"   : "train1_genome_tags_clean.csv",
    "train1_tags"          : "train1_tags_clean.csv",
    "train2_tags"          : "train2_tags_clean.csv",
    "test1_links"          : "test1_links_clean.csv",
}

rating_files = {
    "train3_ratings_full"  : "train3_ratings_full_clean.csv",
    "train1_ratings"       : "train1_ratings_clean.csv",
    "train2_ratings"       : "train2_ratings_clean.csv",
    "train3_ratings_small" : "train3_ratings_small_clean.csv",
    "test1_ratings"        : "test1_ratings_clean.csv",
    "test2_ratings"        : "test2_ratings_clean.csv",
    "train4_small_ratings" : "train4_small_ratings_clean.csv",
}

print()
print("--- MOVIE / METADATA FILES ---")
all_movie_cols = {}
for name, fname in files_to_check.items():
    fpath = os.path.join(PROCESSED, fname)
    if not os.path.exists(fpath):
        print(f"  {name:30s} MISSING")
        continue
    df = pd.read_csv(fpath, nrows=5)
    print(f"  {name:30s} cols={len(df.columns):3d}  -> {list(df.columns)}")
    all_movie_cols[name] = list(df.columns)

print()
print("--- RATING FILES ---")
total_ratings = 0
rating_cols_all = {}
for name, fname in rating_files.items():
    fpath = os.path.join(PROCESSED, fname)
    if not os.path.exists(fpath):
        print(f"  {name:30s} MISSING")
        continue
    df = pd.read_csv(fpath, nrows=5)
    # get row count efficiently
    with open(fpath, "r") as f:
        nrows = sum(1 for _ in f) - 1
    total_ratings += nrows
    print(f"  {name:30s} rows={nrows:>12,}  cols={list(df.columns)}")
    rating_cols_all[name] = list(df.columns)

print()
print("="*70)
print(f"TOTAL RATING ROWS AVAILABLE : {total_ratings:,}")
print("="*70)

print()
print("--- COMMON RATING COLUMNS ---")
all_rc = [set(v) for v in rating_cols_all.values()]
if all_rc:
    common = all_rc[0].intersection(*all_rc[1:])
    print(f"  Common cols across all rating files: {sorted(common)}")

print()
print("--- ALL UNIQUE MOVIE FEATURE COLUMNS ---")
all_cols = set()
for cols in all_movie_cols.values():
    all_cols.update(cols)
for c in sorted(all_cols):
    sources = [n for n,cols in all_movie_cols.items() if c in cols]
    print(f"  {c:35s} in: {sources}")

print()
print("="*70)
print("RECOMMENDATION: which rating files to combine")
print("="*70)
print("  train3_ratings_full  : 26M  - same users/movies as small, FULL version")
print("  train1_ratings       : 20M  - large, different user pool")
print("  train2_ratings       : 27M  - largest, different user pool")
print("  test1/test2_ratings  : 100K - hold out for final evaluation only")
print()
print("  COMBINED USABLE      : 26M + 20M + 27M = ~73M ratings")
