import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:Fajarsyhb0302006@db.xbxlbpnmluobvzqcdxil.supabase.co:5432/postgres"
engine = create_engine(DB_URL)

# STEP 1: Drop semua objek lama 
with engine.connect() as conn:
    conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS mv_gdp_summary CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS fact_economy CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_country CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_time CASCADE;"))
    conn.commit()
print("Drop semua tabel lama ✓")

# STEP 2: Load data bersih 
df = pd.read_csv('clean/worldbank_clean.csv')
print(f"Data siap diload: {df.shape}")

# STEP 3: Load ke tabel utama 
df.to_sql('fact_economy', engine, if_exists='replace', index=False)
print("Tabel fact_economy berhasil dibuat ✓")

# STEP 4: Dim Country 
dim_country = pd.DataFrame({
    'country_code': ['IDN','MYS','THA','SGP','PHL','VNM','MMR','KHM','LAO','BRN'],
    'country_name': ['Indonesia','Malaysia','Thailand','Singapore','Philippines',
                     'Vietnam','Myanmar','Cambodia','Laos','Brunei'],
    'region': ['ASEAN'] * 10
})
dim_country.to_sql('dim_country', engine, if_exists='replace', index=False)
print("Tabel dim_country berhasil dibuat ✓")

# STEP 5: Dim Time 
dim_time = pd.DataFrame({
    'year': [2022, 2023, 2024],
    'quarter': ['Q1', 'Q1', 'Q1'],
    'period': ['2022-Q1', '2023-Q1', '2024-Q1'],
    'year_sequence': [1, 2, 3]
})
dim_time.to_sql('dim_time', engine, if_exists='replace', index=False)
print("Tabel dim_time berhasil dibuat ✓")

# STEP 6: Materialized View 
with engine.connect() as conn:
    conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS mv_gdp_summary CASCADE;"))
    conn.execute(text("""
        CREATE MATERIALIZED VIEW mv_gdp_summary AS
        SELECT
            f.economy,
            d.country_name,
            f.year,
            f.gdp_usd,
            f.inflation_pct,
            f.unemployment_pct,
            f.population
        FROM fact_economy f
        JOIN dim_country d ON f.economy = d.country_code
        ORDER BY f.economy, f.year;
    """))
    conn.commit()
print("Materialized View mv_gdp_summary berhasil dibuat ✓")

# STEP 7: Index 
with engine.connect() as conn:
    conn.execute(text("DROP INDEX IF EXISTS idx_fact_economy;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_fact_year;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_fact_economy_year;"))
    conn.execute(text("CREATE INDEX idx_fact_economy ON fact_economy(economy);"))
    conn.execute(text("CREATE INDEX idx_fact_year ON fact_economy(year);"))
    conn.execute(text("CREATE INDEX idx_fact_economy_year ON fact_economy(economy, year);"))
    conn.commit()
print("Index berhasil dibuat ✓")

# STEP 8: Performance Benchmark
print("\n=== PERFORMANCE BENCHMARK ===")
with engine.connect() as conn:
    print("\n-- Query ke fact_economy (dengan index) --")
    result = conn.execute(text("""
        EXPLAIN ANALYZE
        SELECT economy, AVG(gdp_usd), AVG(inflation_pct)
        FROM fact_economy
        GROUP BY economy;
    """))
    for row in result:
        print(row[0])

    print("\n-- Query ke mv_gdp_summary (materialized view) --")
    result2 = conn.execute(text("""
        EXPLAIN ANALYZE
        SELECT economy, AVG(gdp_usd)
        FROM mv_gdp_summary
        GROUP BY economy;
    """))
    for row in result2:
        print(row[0])

print("\nSemua selesai! ✓")