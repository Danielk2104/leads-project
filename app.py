import streamlit as st
import pandas as pd
from scraper import scrape_leads
from engine import leads_transform
import pydeck as pdk

st.set_page_config(page_title="Lead Gen King", layout="wide", page_icon="💎")

if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = None

# Makes the UI for lead generator and the sample csv pages 
def render_lead_dashboard(df_final, leads_wanted, niche, city):
    df_final = df_final.drop_duplicates(subset=['Name', 'Phone'], keep='first')  
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total leads", len(df_final), help=f"{leads_wanted - len(df_final)} duplicates removed")
    col2.metric("Average city rating", value=f"{round(df_final['Rating'].mean(), 2)} ⭐")
    col3.metric("Median reviews", value=f"{round(df_final['Reviews'].median(), 2)} 💬")

    no_website_count = (
        df_final['Website'].isna() |
        (df_final['Website'] == '') |
        (df_final['Website'].astype(str).str.upper() == 'N/A')
    ).sum()

    col4.metric(
        label="Leads with No Website",
        value=int(no_website_count),
        delta="High-Value Targets",
        delta_color="inverse"
    )

    st.subheader("Lead List")
    
    # Sort and clean dataset
    df_sorted = df_final[['Name', 'Rating', 'Reviews', 'Phone', 'Website', 'Address', 'LeadScore']].sort_values(by="LeadScore", ascending=False)
    df_sorted["Website"] = df_sorted["Website"].astype(str).str.strip()
    df_sorted["Website"] = df_sorted["Website"].replace(["nan", "None", "", "n/a", "N/A"], None)
    df_sorted["Website"] = df_sorted["Website"].fillna("")

    df_display = df_sorted.copy()
    df_display.insert(0, "Select", False)
   
    edited_df = st.data_editor(
        df_display,
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", help="Check boxes to build a custom curated download list."),
            "Name": st.column_config.TextColumn("Business Name", help="Name on Google Maps", width="medium"),
            "LeadScore": st.column_config.ProgressColumn(
                "Opportunity Score",
                help="Higher score means the lead has better ratings and more reviews compared to other leads",
                format="%d", min_value=0, max_value=100,
            ),
            "Rating": st.column_config.NumberColumn("Rating", format="%.1f ⭐"),
            "Reviews": st.column_config.NumberColumn("Total Reviews", format="%d 💬"),
            "Website": st.column_config.LinkColumn("Website Link", display_text="Visit Site"),
            "Phone": st.column_config.TextColumn("Contact Number"),
            "Address": st.column_config.TextColumn("Street Address", width="medium")
        },
        hide_index=True,
        use_container_width=True
    )

    with st.expander("Lead score deep dive"):
        names_list = [""] + df_final["Name"].astype(str).tolist()
        selected_lead = st.selectbox("Search for a lead to analyse score", names_list, key="lead_search_deep_dive")
   
        if selected_lead and selected_lead != "":
            lead_data = df_final[df_final["Name"] == selected_lead].iloc[0]
       
            beaten_reviews = len(df_final[df_final["Reviews"] < lead_data["Reviews"]])
            tied_reviews = len(df_final[df_final["Reviews"] == lead_data["Reviews"]]) - 1
            rev_perc = (beaten_reviews / len(df_final)) * 100
       
            beaten_ratings = len(df_final[df_final["Rating"] < lead_data["Rating"]])
            tied_ratings = len(df_final[df_final["Rating"] == lead_data["Rating"]]) - 1
            rat_perc = (beaten_ratings / len(df_final)) * 100

            st.metric("Overall Lead Score", f"{lead_data['LeadScore']}/100")
            st.subheader("Market Standing")
       
            st.write(f"💬 **Reviews: {lead_data['Reviews']}**")
            st.write(f"- Beats **{beaten_reviews}** competitors.")
            st.write(f"- Ties with **{tied_reviews}** competitors.")
            st.info(f"Top **{100 - int(rev_perc)}%** of leads generated.")
       
            st.divider()

            st.write(f"⭐ **Rating: {lead_data['Rating']}**")
            st.write(f"- Beats **{beaten_ratings}** competitors.")
            st.write(f"- Ties with **{tied_ratings}** competitors.")
            st.info(f"Top **{100 - int(rat_perc)}%** of leads generated.")

            st.divider()
       
            st.write("### Modifier Breakdown")
            reasons = lead_data.get("ScoreReasons", [])
            if not reasons:
                st.warning("No reasons found in data. Check engine column names.")
            else:
                for r in reasons:
                    st.write(r)
                    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Market Geography")
    
    map_col, guide_col = st.columns([2, 1])
    with map_col:
        map_df = df_final.copy().rename(columns={'Lat': 'lat', 'Lng': 'lon'}).dropna(subset=['lat', 'lon'])
        map_df = map_df[(map_df['lat'] != 0) & (map_df['lon'] != 0)]
        map_df['lat'] = pd.to_numeric(map_df['lat'], errors='coerce')
        map_df['lon'] = pd.to_numeric(map_df['lon'], errors='coerce')
        lead_name = st.selectbox("Select a lead to locate", ["All"] + list(df_final["Name"]))
       
        if lead_name != "All":
            plot_df = map_df[map_df["Name"] == lead_name]
            row = plot_df.iloc[0]
            centre_lat = row['lat']
            centre_lon = row['lon']
            zoom_level = 15
        else:
            centre_lat = map_df["lat"].mean()
            centre_lon = map_df["lon"].mean()
            zoom_level = 11
            plot_df = map_df
       
        if not map_df.empty:
            layer = pdk.Layer(
                "ScatterplotLayer",
                plot_df,
                get_position='[lon, lat]',
                get_color='colour',
                get_radius=10,
                radius_min_pixels=6,      
                radius_max_pixels=15,
                stroked=True,
                line_width_min_pixels=1,
                get_line_color=[255, 255, 255],
                pickable=True,
            )

            view_state = pdk.ViewState(
                latitude=centre_lat,
                longitude=centre_lon,
                zoom=zoom_level,
                pitch=0,
            )

            st.pydeck_chart(pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "{Name}\nScore: {LeadScore}\nPhone: {Phone}"}
            ))
        else:
            st.info("No coordinate data available for these leads.")
   
    with guide_col:
        st.subheader("Scoring Framework")
        with st.expander("How are leads prioritized?", expanded=True):
            st.markdown("""
                Leads are rated between **0 to 100**:
                *   **80+ (Market Leaders):** These leads have the highest ratings and reviews and has a website and phone number
                *   **50-79 (Medium Opportunity):** Good foundation but ratings/reviews aren't as high compared to others, website/phone number may be missing
                *   **Under 50 (Under established leads):** These leads may have less reviews/lower ratings/missing phone number or website. (Potential sales opportunity)
                """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Export Lead Data")
    btn_col1, btn_col2 = st.columns(2)
    csv_all = df_final.to_csv(index=False).encode('utf-8')
    btn_col1.download_button(
        label="Download All Found Leads",
        data=csv_all,
        file_name=f"all_leads_{city}_{niche}.csv",
        mime='text/csv',
        use_container_width=True,
        icon=":material/download:"
    )
    
    selected_rows = edited_df[edited_df["Select"] == True]
    if not selected_rows.empty:
        clean_selected_df = selected_rows.drop(columns=["Select"])
        csv_selected = clean_selected_df.to_csv(index=False).encode('utf-8')
        btn_col2.download_button(
            label=f"Download Selected Leads ({len(selected_rows)})",
            data=csv_selected,
            file_name=f"curated_leads_{city}_{niche}.csv",
            mime='text/csv',
            use_container_width=True,
            icon=":material/done:"
        )
    else:
        btn_col2.button(
            label="Download Selected Leads (0)",
            disabled=True,
            use_container_width=True,
            help="Check the checkbox next to a lead in the table above to download a filtered target list."
        )

st.sidebar.title("Navigation Menu")
app_mode = st.sidebar.radio(
    "Choose Screen Mode:",
    ["🏠 Home & Instructions", "📊 Demo Mode (Pre-loaded CSV)", "💎 Live Lead Generator"]
)
st.sidebar.divider()

# Home Page
if app_mode == "🏠 Home & Instructions":
    st.title("Lead Gen King - lead generator tool")
    st.markdown("Find leads from Google Maps in one place with competitive lead scoring.")       
    
    st.markdown("### 👋 Welcome to Lead Gen King")
    st.markdown("Your centralised workspace for Google Maps leads. To get started, view the sample csv to see how the app works or go to the live generator")
    
    st.markdown("#### How it works")
    step1, step2, step3 = st.columns(3)
   
    with step1:
        st.markdown("""
        <div style="background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #60A5FA;">
            <h3>1. Target</h3>
            <p>Enter your niche and location (<b>Tip write location in this format: city/county/state, country</b>) in the sidebar settings.</p>
        </div>
        """, unsafe_allow_html=True)
       
    with step2:
        st.markdown("""
        <div style="background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #F59E0B;">
            <h3>2. Analyse</h3>
            <p>Select the number of leads you want and get the nearest leads as a list and their lead scores. <b>20 leads use 1 API credit! </b></p>
        </div>
        """, unsafe_allow_html=True)
       
    with step3:
        st.markdown("""
        <div style="background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #10B981;">
            <h3>3. Export</h3>
            <p>Review market standing metrics, locate leads geographically and download a CSV lead list instantly.</p>
        </div>
        """, unsafe_allow_html=True)

# Sample CSV page
elif app_mode == "📊 Demo Mode (Pre-loaded CSV)":
    st.title("Demo Lead Generator using a free example CSV (Plumbers in London, UK)")
    st.markdown("This is how the app works with live leads from SerpAPI with a free CSV")
    
    try:
        df_raw = pd.read_csv("public_demo_data.csv")
        df_demo_processed = leads_transform(df_raw)
        render_lead_dashboard(df_demo_processed, leads_wanted=len(df_demo_processed), niche="Example Niche", city="Example City")
        
    except Exception as e:
        st.error("Missing CSV")

# Live Lead Gen page
elif app_mode == "💎 Live Lead Generator":
    st.title("Live Local Lead Generation tool")
    st.markdown("Finding real-time local leads via the SerpAPI Google Maps endpoint.")
    st.sidebar.subheader("settings")
    api_key = st.sidebar.text_input("Enter your SerpAPI key", type="password")
    niche = st.sidebar.text_input("Enter your niche")
    city = st.sidebar.text_input("Enter your location",help="Enter location as city/county/state, country **(eg: London, UK)**")
    
    leads_wanted = st.sidebar.slider("How many leads would you like to see?", min_value=20, max_value=100, step=20, value=20)
    search_depth = leads_wanted // 20
    search_button = st.sidebar.button(" **Fetch leads**", use_container_width=True)
    
    st.sidebar.info("High lead counts may produce duplicate results eg: if you scrape 60 leads you may only see 58!")

    if search_button:
        if not niche or not city:
            st.warning("Please enter a niche and city")
        else:
            with st.spinner(f"Scraping leads in {city} for {niche}..."):
                raw_data = scrape_leads(niche, city, api_key, search_depth)
       
                if raw_data:
                    df_raw = pd.DataFrame(raw_data)
                    st.session_state["leads_data"] = leads_transform(df_raw)
                    st.success("Data collection complete, see leads below")
                else:
                    st.warning("No live leads captured.")

    if st.session_state["leads_data"] is not None:
        render_lead_dashboard(st.session_state["leads_data"], leads_wanted, niche, city)
    else:
        st.info("Please enter your SerpAPI key, niche, location and how many leads you want in the sidebar")   