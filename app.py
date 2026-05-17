import streamlit as st
import pandas as pd
from scraper import scrape_leads
from engine import leads_transform
import pydeck as pdk

if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = None


st.set_page_config(page_title="Lead Gen King",layout="wide",page_icon="💎")

st.sidebar.header("Settings")
use_csv = st.sidebar.checkbox("Use example csv")

api_key = st.sidebar.text_input("Enter your SerpAPI key",type="password")
niche = st.sidebar.text_input("Enter your profession")
city = st.sidebar.text_input("Enter your city")
leads_wanted = st.sidebar.slider("How many leads would you like to see?",min_value=20,max_value=100,step=20,value=20)
search_depth = leads_wanted // 20
search_button = st.sidebar.button(" **Fetch leads**", use_container_width=True)
st.sidebar.divider()
st.sidebar.info("💡 **Tip:** High lead counts take a few extra seconds to parse and score.")

if search_button:
    if use_csv:
        try:
            df_raw = pd.read_csv("public_demo_data.csv")
            st.session_state['leads_data'] = leads_transform(df_raw)
        except Exception as e:
            st.error("No cached data")
    else:
        if not niche or not city:
            st.warning("Please enter a niche and city")
        else:
            with st.spinner(f"Scraping leads in {city} for {niche}"):
                raw_data = scrape_leads(niche,city,api_key,search_depth)
        
                if raw_data:
                    df_raw = pd.DataFrame(raw_data)
                    st.session_state["leads_data"] = leads_transform(df_raw)
                else:
                    st.warning("No leads found")
                    
st.title("Lead Gen King - lead generator tool")
st.markdown("Find leads from Google Maps in one place with competitive lead scoring.")                 
    
if st.session_state["leads_data"] is not None:
    df_final = st.session_state["leads_data"]   
        # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total leads", len(df_final))
    col2.metric("Average city rating", value= f"{round(df_final['Rating'].mean(),2)} ⭐")
    col3.metric("Median reviews", value= f"{round(df_final['Reviews'].median(),2)} 💬") 
    st.divider()
        # Lead table
    st.subheader("Lead List")
    df_sorted = df_final[['Name','Rating','Reviews','Phone','Website','Address','LeadScore']].sort_values(by="LeadScore",ascending=False)
    df_sorted["Website"] = df_sorted["Website"].astype(str).str.strip()
    df_sorted["Website"] = df_sorted["Website"].replace(["nan", "None", "","n/a","N/A"], None)
    df_sorted["Website"] = df_sorted["Website"].fillna("")
    
    st.dataframe(
            df_sorted,
            column_config={
                "Name": st.column_config.TextColumn("Business Name", help="Name on Google Maps", width="medium"),
                "LeadScore": st.column_config.ProgressColumn(
                    "Opportunity Score",
                    help="Higher score means the lead has better ratings and more reviews",
                    format="%d",
                    min_value=0,
                    max_value=100,
                ),
                "Rating": st.column_config.NumberColumn("Rating", format="%.1f ⭐"),
                "Reviews": st.column_config.NumberColumn("Total Reviews", format="%d 💬"),
                "Website": st.column_config.LinkColumn("Website Link",display_text="Visit Site"),
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
            st.subheader(" Market Standing")
        
            st.write(f"💬 **Reviews: {lead_data['Reviews']}**")
            st.write(f"- Beats **{beaten_reviews}** competitors.")
            st.write(f"- Ties with **{tied_reviews}** competitors.")
            st.info(f"Top **{100 - int(rev_perc)}%** of the local market.")
        
            st.divider()

            st.write(f"⭐ **Rating: {lead_data['Rating']}**")
            st.write(f"- Beats **{beaten_ratings}** competitors.")
            st.write(f"- Ties with **{tied_ratings}** competitors.")
            st.info(f"Top **{100 - int(rat_perc)}%** of the local market.")

            st.divider()
        
            st.write("### Modifier Breakdown")
            reasons = lead_data.get("ScoreReasons", [])
            if not reasons:
                st.warning("No reasons found in data. Check engine column names.")
            else:
                for r in reasons:
                    st.write(r)
                    

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📍 Market Geography")
    
    map_col, guide_col = st.columns([2, 1])
    with map_col:
        map_df = df_final.copy().rename(columns={'Lat': 'lat', 'Lng': 'lon'}).dropna(subset=['lat', 'lon'])
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
            get_line_color=[255,255,255],
            pickable=True, 
        )

            view_state = pdk.ViewState(
            latitude= centre_lat,
            longitude= centre_lon,
            zoom= zoom_level,
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
        st.subheader("📈 Scoring Framework")
        with st.expander("How are leads prioritized?", expanded=True):
            st.markdown("""
                Leads are rated between **0 to 100**:
                *   **80+ (Market Leaders):** These leads have the highest ratings and reviews and has a website and phone number
                *   **50-79 (Medium Opportunity):** Good foundation but ratings/reviews aren't as high compared to others, website/phone number may be missing
                *   **Under 50 (Under established leads):** These leads may have less reviews/lower ratings/missing phone number or website. (Potential sales opportunity)
                """)
        
    _,btn_col = st.columns([4,1])
    with btn_col:
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Leads",
            data = csv,
            file_name = f"leads_{city}_and_{niche}.csv",
            mime = 'text/csv',
            use_container_width=True,
            icon=":material/download:"
        )

else: 
    st.markdown("### 👋 Welcome to Lead Gen King")
    st.markdown("Your centralised workspace for Google Maps leads. To get started, configure your target market in the sidebar on the left.")
    st.space = st.write("")
    
    st.markdown("#### How it works")
    step1, step2, step3 = st.columns(3)
    
    with step1:
        st.markdown("""
        <div style="background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #60A5FA;">
            <h3>1. Target</h3>
            <p>Enter your business and location in the sidebar settings (eg: Bakeries in London).</p>
        </div>
        """, unsafe_allow_html=True)
        
    with step2:
        st.markdown("""
        <div style="background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #F59E0B;">
            <h3>2. Analyse</h3>
            <p>Select the number of leads you want and get the list and their lead scores. <b>20 leads use 1 API credit! </b></p>
        </div>
        """, unsafe_allow_html=True)
        
    with step3:
        st.markdown("""
        <div style="background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #10B981;">
            <h3>3. Export</h3>
            <p>Review market standing metrics, locate leads geographically and download a CSV lead list instantly.</p>
        </div>
        """, unsafe_allow_html=True)
        
        
        