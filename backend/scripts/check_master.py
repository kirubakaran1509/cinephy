import pandas as pd
MASTER = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed\master_movies.csv'
df = pd.read_csv(MASTER)
print('Shape:', df.shape)
print('\nNulls:')
print(df.isnull().sum())
print('\nSample cast_list:')
print(df['cast_list'].head(5).tolist())
print('\nSample director:')
print(df['director'].head(5).tolist())
print('\nSample keyword_list:')
print(df['keyword_list'].head(5).tolist())
print('\nRating stats:')
print(df[['avg_rating','rating_count','weighted_score']].describe())
