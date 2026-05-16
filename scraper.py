import requests
import streamlit as st

@st.cache_data(show_spinner=False)
def scrape_leads(profession, city, api_key, pages=1):
    all_leads = []
    
    for i in range(pages):
        start_index = i * 20
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_maps",
            "q": f"{profession} in {city}",
            "api_key": api_key,
            "start": start_index,
            "type": "search"
        }

        try:
            print(f"Fetching page {i+1}...")
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if "error" in data:
                print(f"API Error: {data['error']}")
                break
                
            raw_results = data.get("local_results", [])
            
            if not raw_results:
                print("No more results found.")
                break

            for lead in raw_results:
                all_leads.append({
                    "Name": lead.get("title", "N/A"),
                    "Rating": lead.get("rating", 0.0),
                    "Reviews": lead.get("reviews", 0),
                    "Phone": lead.get("phone", "N/A"),
                    "Website": lead.get("website", "N/A"),
                    "Address": lead.get("address", "N/A"),
                    "Lat": lead.get("gps_coordinates", {}).get("latitude"),
                    "Lng": lead.get("gps_coordinates", {}).get("longitude"),
                })
            
        except Exception as e:
            print(f"Connection Error: {e}")
            break
            
    return all_leads