import pandas as pd, os
PROC = r'C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed'
kw = pd.read_csv(os.path.join(PROC, 'train3_keywords_clean.csv'), nrows=3)
print('COLUMNS:', list(kw.columns))
print(kw.head(3))
