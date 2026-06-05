import pandas as pd
import numpy as np
import os

# 1. Load data 
df = pd.read_csv('staging/raw_worldbank.csv')
print("=== DATA AWAL ===")
print(df.shape)
print(df.head())

# 2. Reshape: wide → long format 
df_long = df.melt(
    id_vars=['economy', 'series'],
    value_vars=['YR2022', 'YR2023', 'YR2024'],
    var_name='year_raw',
    value_name='value'
)

# Ekstrak angka tahun dari 'YR2022' → 2022
df_long['year'] = df_long['year_raw'].str.extract(r'(\d{4})').astype(int)
df_long = df_long.drop(columns=['year_raw'])

print("\n=== SETELAH RESHAPE ===")
print(df_long.shape)
print(df_long.head(10))

# 3. Pivot: tiap indikator jadi kolom sendiri
df_pivot = df_long.pivot_table(
    index=['economy', 'year'],
    columns='series',
    values='value',
    aggfunc='first'
).reset_index()

# Rename kolom indikator
df_pivot = df_pivot.rename(columns={
    'NY.GDP.MKTP.CD': 'gdp_usd',
    'FP.CPI.TOTL.ZG': 'inflation_pct',
    'SL.UEM.TOTL.ZS': 'unemployment_pct',
    'SP.POP.TOTL':    'population'
})
df_pivot.columns.name = None

print("\n=== SETELAH PIVOT ===")
print(df_pivot.shape)
print(df_pivot.head(10))

# 4. Anomaly Detection 
print("\n=== MISSING VALUES ===")
print(df_pivot.isnull().sum())

print(f"\nJumlah duplikat: {df_pivot.duplicated().sum()}")

# 5. Handle missing values (imputasi median) 
num_cols = ['gdp_usd', 'inflation_pct', 'unemployment_pct', 'population']
missing_before = df_pivot.isnull().sum().sum()

for col in num_cols:
    if col in df_pivot.columns:
        df_pivot[col] = df_pivot[col].fillna(df_pivot[col].median())

missing_after = df_pivot.isnull().sum().sum()
print(f"\nMissing values: {missing_before} → {missing_after} (setelah imputasi median)")

# 6. Deteksi outlier IQR 
print("\n=== OUTLIER (IQR METHOD) ===")
for col in num_cols:
    if col in df_pivot.columns:
        Q1 = df_pivot[col].quantile(0.25)
        Q3 = df_pivot[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df_pivot[
            (df_pivot[col] < Q1 - 1.5*IQR) |
            (df_pivot[col] > Q3 + 1.5*IQR)
        ]
        print(f"{col}: {len(outliers)} outlier terdeteksi")

# 7. Tambah kolom time granularity 
df_pivot['quarter'] = 'Q1'
df_pivot['period']  = df_pivot['year'].astype(str) + '-Q1'

# 8. Simpan 
os.makedirs('clean', exist_ok=True)
df_pivot.to_csv('clean/worldbank_clean.csv', index=False)

print("\n=== DATA BERSIH FINAL ===")
print(df_pivot.shape)
print(df_pivot.head(10))
print("\nDisimpan ke clean/worldbank_clean.csv ✓")