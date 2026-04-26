import pandas as pd
import numpy as np
import os

PROCESSED = r"C:\Users\kirub\OneDrive\Desktop\movie\backend\data\processed"

print("="*70)
print("COMPLETE COLUMN AUDIT - EVERY FILE EVERY COLUMN WITH SAMPLE VALUES")
print("="*70)

files = sorted(os.listdir(PROCESSED))
for fname in files:
    if not fname.endswith(".csv"):
        continue
    fpath = os.path.join(PROCESSED, fname)
    size  = os.path.getsize(fpath)/1024/1024
    try:
        df = pd.read_csv(fpath, nrows=3)
        with open(fpath) as f:
            nrows = sum(1 for _ in f) - 1
        print(f"\n{'='*70}")
        print(f"FILE : {fname}")
        print(f"ROWS : {nrows:,}   SIZE: {size:.1f} MB   COLS: {len(df.columns)}")
        print(f"{'='*70}")
        for col in df.columns:
            sample = df[col].tolist()
            dtype  = str(df[col].dtype)
            nulls  = df[col].isna().sum()
            print(f"  {col:35s} dtype={dtype:10s} nulls={nulls}  sample={sample}")
    except Exception as e:
        print(f"\nFILE : {fname}  ERROR: {e}")

print("\n" + "="*70)
print("SUMMARY TABLE")
print("="*70)
print(f"{'FILE':50s} {'ROWS':>12} {'COLS':>6} {'MB':>8}")
print("-"*80)
total_rows = 0
for fname in files:
    if not fname.endswith(".csv"):
        continue
    fpath = os.path.join(PROCESSED, fname)
    size  = os.path.getsize(fpath)/1024/1024
    try:
        df = pd.read_csv(fpath, nrows=1)
        with open(fpath) as f:
            nrows = sum(1 for _ in f) - 1
        total_rows += nrows
        print(f"  {fname:48s} {nrows:>12,} {len(df.columns):>6} {size:>8.1f}")
    except Exception as e:
        print(f"  {fname:48s} ERROR: {e}")
print(f"\n  TOTAL ROWS : {total_rows:,}")
