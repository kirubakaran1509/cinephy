import os
import pandas as pd

PROCESSED = r"C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed"
RAW       = r"C:\Users\kirub\OneDrive\Desktop\movie\backend\data\raw"

print("="*60)
print("ALL PROCESSED FILES")
print("="*60)
total_rows = 0
for fname in sorted(os.listdir(PROCESSED)):
    fpath = os.path.join(PROCESSED, fname)
    size  = os.path.getsize(fpath) / 1024 / 1024
    if fname.endswith(".csv"):
        try:
            df = pd.read_csv(fpath)
            print(f"  {fname:45s} {len(df):>10,} rows  {size:.1f} MB")
            if "rating" in fname.lower() or "ratings" in [c.lower() for c in df.columns]:
                total_rows += len(df)
        except:
            print(f"  {fname:45s} ERROR reading  {size:.1f} MB")
    else:
        print(f"  {fname:45s} {size:.1f} MB")

print()
print(f"  TOTAL rating rows found : {total_rows:,}")

print()
print("="*60)
print("ALL RAW FILES")
print("="*60)
for fname in sorted(os.listdir(RAW)):
    fpath = os.path.join(RAW, fname)
    size  = os.path.getsize(fpath) / 1024 / 1024
    print(f"  {fname:45s} {size:.1f} MB")
