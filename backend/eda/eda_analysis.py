import warnings
warnings.filterwarnings('ignore')
import os, ast
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

PROC    = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
OUTDIR  = os.path.join(os.path.dirname(__file__), 'charts')
os.makedirs(OUTDIR, exist_ok=True)

print('Loading master dataset...')
master = pd.read_csv(os.path.join(PROC, 'master_movies.csv'))

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

sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams['figure.dpi'] = 120

def save(name):
    path = os.path.join(OUTDIR, name)
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print('Saved:', path)

# Chart 1 — Vote average distribution
print('Chart 1: Vote average distribution')
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(master['vote_average'].dropna(), bins=40, color='steelblue', edgecolor='white')
ax.set_title('Distribution of Vote Averages')
ax.set_xlabel('Vote Average')
ax.set_ylabel('Number of Movies')
save('01_vote_average_distribution.png')

# Chart 2 — Weighted score distribution
print('Chart 2: Weighted score distribution')
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(master['weighted_score'].dropna(), bins=40, color='darkorange', edgecolor='white')
ax.set_title('Distribution of Weighted Scores (IMDB Formula)')
ax.set_xlabel('Weighted Score')
ax.set_ylabel('Number of Movies')
save('02_weighted_score_distribution.png')

# Chart 3 — Movies per year
print('Chart 3: Movies per year')
year_counts = master['year'].dropna().astype(int).value_counts().sort_index()
year_counts = year_counts[year_counts.index >= 1950]
fig, ax = plt.subplots(figsize=(14, 5))
ax.bar(year_counts.index, year_counts.values, color='teal', edgecolor='white', width=0.8)
ax.set_title('Number of Movies Released per Year')
ax.set_xlabel('Year')
ax.set_ylabel('Number of Movies')
save('03_movies_per_year.png')

# Chart 4 — Top 15 genres
print('Chart 4: Top genres')
all_genres = []
for g in master['genre_list'].dropna():
    all_genres.extend(parse_list(g))
genre_counts = pd.Series(all_genres).value_counts().head(15)
fig, ax = plt.subplots(figsize=(12, 6))
genre_counts.sort_values().plot(kind='barh', ax=ax, color='mediumpurple')
ax.set_title('Top 15 Genres by Movie Count')
ax.set_xlabel('Number of Movies')
save('04_top_genres.png')

# Chart 5 — Vote count distribution (log scale)
print('Chart 5: Vote count distribution')
fig, ax = plt.subplots(figsize=(10, 5))
vc = master['vote_count'].dropna()
vc = vc[vc > 0]
ax.hist(np.log10(vc), bins=40, color='salmon', edgecolor='white')
ax.set_title('Vote Count Distribution (log10 scale)')
ax.set_xlabel('log10(Vote Count)')
ax.set_ylabel('Number of Movies')
save('05_vote_count_distribution.png')

# Chart 6 — Top 15 directors by movie count
print('Chart 6: Top directors')
dir_counts = master['director'].dropna().value_counts().head(15)
fig, ax = plt.subplots(figsize=(12, 6))
dir_counts.sort_values().plot(kind='barh', ax=ax, color='cornflowerblue')
ax.set_title('Top 15 Directors by Number of Movies')
ax.set_xlabel('Number of Movies')
save('06_top_directors.png')

# Chart 7 — Average weighted score by genre
print('Chart 7: Avg score by genre')
genre_scores = {}
for _, row in master.iterrows():
    genres = parse_list(row.get('genre_list', ''))
    score  = row.get('weighted_score', np.nan)
    if pd.isna(score):
        continue
    for g in genres:
        genre_scores.setdefault(g, []).append(float(score))
avg_genre = pd.Series({g: np.mean(v) for g, v in genre_scores.items() if len(v) >= 10})
avg_genre = avg_genre.sort_values(ascending=False).head(15)
fig, ax = plt.subplots(figsize=(12, 6))
avg_genre.sort_values().plot(kind='barh', ax=ax, color='mediumseagreen')
ax.set_title('Average Weighted Score by Genre (min 10 movies)')
ax.set_xlabel('Average Weighted Score')
save('07_avg_score_by_genre.png')

# Chart 8 — Runtime distribution
print('Chart 8: Runtime distribution')
rt = master['runtime'].dropna()
rt = rt[(rt > 30) & (rt < 300)]
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(rt, bins=40, color='goldenrod', edgecolor='white')
ax.set_title('Movie Runtime Distribution')
ax.set_xlabel('Runtime (minutes)')
ax.set_ylabel('Number of Movies')
save('08_runtime_distribution.png')

# Chart 9 — Popularity distribution (log scale)
print('Chart 9: Popularity distribution')
pop = master['popularity'].dropna()
pop = pop[pop > 0]
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(np.log10(pop), bins=40, color='tomato', edgecolor='white')
ax.set_title('Popularity Distribution (log10 scale)')
ax.set_xlabel('log10(Popularity)')
ax.set_ylabel('Number of Movies')
save('09_popularity_distribution.png')

# Chart 10 — Vote average vs weighted score scatter
print('Chart 10: Vote avg vs weighted score')
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(master['vote_average'], master['weighted_score'],
           alpha=0.3, s=10, color='steelblue')
ax.set_title('Vote Average vs Weighted Score')
ax.set_xlabel('Vote Average')
ax.set_ylabel('Weighted Score')
save('10_vote_vs_weighted.png')

# Chart 11 — Top 15 languages
print('Chart 11: Top languages')
lang_counts = master['original_language'].dropna().value_counts().head(15)
fig, ax = plt.subplots(figsize=(12, 6))
lang_counts.sort_values().plot(kind='barh', ax=ax, color='orchid')
ax.set_title('Top 15 Languages by Movie Count')
ax.set_xlabel('Number of Movies')
save('11_top_languages.png')

# Chart 12 — Avg rating count by decade
print('Chart 12: Avg rating count by decade')
master['decade'] = (master['year'].dropna().astype(int) // 10 * 10)
decade_avg = master.groupby('decade')['rating_count'].mean().dropna()
decade_avg = decade_avg[decade_avg.index >= 1950]
fig, ax = plt.subplots(figsize=(12, 5))
decade_avg.plot(kind='bar', ax=ax, color='cadetblue', edgecolor='white')
ax.set_title('Average User Rating Count by Decade')
ax.set_xlabel('Decade')
ax.set_ylabel('Avg Rating Count')
plt.xticks(rotation=45)
save('12_rating_count_by_decade.png')

print()
print('All 12 charts saved to:', OUTDIR)
