from scraper import scrape_leads
import pandas as pd

API_KEY = "116476dd0c9be208c215e12dd608d205a8e62ec8e72e723ebd4ae09f2f86f7eb" 
PROFESSION = "Plumbers"
CITY = "London"

print(f"Starting search for {PROFESSION} in {CITY}...")
raw_data = scrape_leads(PROFESSION, CITY, API_KEY, pages=2) 

if raw_data:
    df = pd.DataFrame(raw_data)
    print(f"\nSuccessfully collected {len(df)} leads.")
    print(df[['Name', 'Rating', 'Reviews']].head()) # Show top 5
    df.to_csv("leads_cache.csv", index=False)
    print("\nData saved to leads_cache.csv")
else:
    print("No data collected.")