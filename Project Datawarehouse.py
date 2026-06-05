import wbgapi as wb
import pandas as pd
import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

indicators = {
    'NY.GDP.MKTP.CD': 'gdp_usd',
    'FP.CPI.TOTL.ZG': 'inflation_pct',
    'SL.UEM.TOTL.ZS': 'unemployment_pct',
    'SP.POP.TOTL': 'population'
}

countries = ['IDN','MYS','THA','SGP','PHL','VNM','MMR','KHM','LAO','BRN']

async def fetch_and_stage():
    print("Fetching data dari World Bank API...")
    df = wb.data.DataFrame(
        list(indicators.keys()),
        economy=countries,
        time=range(2022, 2025)
    ).reset_index()
    df = df.rename(columns=indicators)
    os.makedirs('staging', exist_ok=True)
    df.to_csv('staging/raw_worldbank.csv', index=False)
    print(f"Selesai! {df.shape[0]} baris tersimpan di staging/raw_worldbank.csv")

async def main():
    await fetch_and_stage()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_stage, 'interval', hours=24)
    scheduler.start()
    print("Scheduler aktif, fetch ulang tiap 24 jam...")

    await asyncio.sleep(86400)

if __name__ == '__main__':
    asyncio.run(main())