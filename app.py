import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# Setup Page Configuration
st.set_page_config(page_title="PhonePe Pulse Reimagined", layout="wide", initial_sidebar_state="expanded")

# Custom UI styling to mimic premium PhonePe aesthetics (dark mode by default logic)
st.markdown("""
    <style>
    /* Premium Native-friendly UI */
    .stSelectbox label, .stRadio label {font-weight: 600;}
    div[data-testid="metric-container"] {
        background-color: rgba(106, 27, 154, 0.05); 
        border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        margin-bottom: 20px;
        border-left: 4px solid #6a1b9a;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px; font-weight: 700; color: #6a1b9a;
    }
    hr {margin: 1.5em 0; border: 0; height: 1px; background-image: linear-gradient(to right, rgba(106, 27, 154, 0), rgba(106, 27, 154, 0.5), rgba(106, 27, 154, 0));}
    </style>
""", unsafe_allow_html=True)

# GeoJSON Loading
@st.cache_data
def load_geojson():
    try:
        with open(os.path.join(BASE, "india_states.geojson"), "r") as f:
            return json.load(f)
    except Exception as e:
        st.warning("GeoJSON for maps not found. Map visuals will be limited.")
        return None

india_geojson = load_geojson()

# Database Connection
@st.cache_resource
def get_connection():
    return sqlite3.connect(os.path.join(BASE, "pulse.db"), check_same_thread=False)

conn = get_connection()

# State Mapping Dictionary
state_mapping = {
    'andaman-&-nicobar-islands': 'Andaman & Nicobar', 'andhra-pradesh': 'Andhra Pradesh',
    'arunachal-pradesh': 'Arunachal Pradesh', 'assam': 'Assam', 'bihar': 'Bihar',
    'chandigarh': 'Chandigarh', 'chhattisgarh': 'Chhattisgarh', 
    'dadra-&-nagar-haveli-&-daman-&-diu': 'Dadra and Nagar Haveli and Daman and Diu', 'delhi': 'Delhi',
    'goa': 'Goa', 'gujarat': 'Gujarat', 'haryana': 'Haryana', 'himachal-pradesh': 'Himachal Pradesh',
    'jammu-&-kashmir': 'Jammu & Kashmir', 'jharkhand': 'Jharkhand', 'karnataka': 'Karnataka',
    'kerala': 'Kerala', 'ladakh': 'Ladakh', 'lakshadweep': 'Lakshadweep', 'madhya-pradesh': 'Madhya Pradesh',
    'maharashtra': 'Maharashtra', 'manipur': 'Manipur', 'meghalaya': 'Meghalaya', 'mizoram': 'Mizoram',
    'nagaland': 'Nagaland', 'odisha': 'Odisha', 'puducherry': 'Puducherry', 'punjab': 'Punjab',
    'rajasthan': 'Rajasthan', 'sikkim': 'Sikkim', 'tamil-nadu': 'Tamil Nadu', 'telangana': 'Telangana',
    'tripura': 'Tripura', 'uttar-pradesh': 'Uttar Pradesh', 'uttarakhand': 'Uttarakhand', 'west-bengal': 'West Bengal'
}

# Reverse mapping: display name -> slug (used for district queries)
reverse_state_mapping = {v: k for k, v in state_mapping.items()}

# Queries Generator
def fetch_data(query, conn):
    try:
        return pd.read_sql(query, conn)
    except Exception as e:
        return pd.DataFrame()

# Sidebar
st.sidebar.markdown("<h2 style='color: #6a1b9a; text-align: center'>PhonePe Pulse</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.title("Explorer")

domain = st.sidebar.radio("Select Domain", ["Transactions", "Users", "Insurance"])

# Fetch available years
df_years = fetch_data("SELECT DISTINCT Year FROM Aggregated_transaction ORDER BY Year", conn)
available_years = df_years['Year'].tolist() if not df_years.empty else [2018, 2019, 2020, 2021, 2022, 2023, 2024]
selected_year = st.sidebar.selectbox("Select Year", available_years)

selected_quarter = st.sidebar.selectbox("Select Quarter", [1, 2, 3, 4])

st.title(f"PhonePe Pulse - {domain} ({selected_year} Q{selected_quarter})")

# ── TRANSACTIONS ──────────────────────────────────────────────────────────────
if domain == "Transactions":
    # 1. Total Metrics
    agg_query = f"SELECT SUM(Transaction_count) as Total_Count, SUM(Transaction_amount) as Total_Amount FROM Aggregated_transaction WHERE Year={selected_year} AND Quarter={selected_quarter}"
    agg_df = fetch_data(agg_query, conn)
    
    col1, col2 = st.columns(2)
    with col1:
        count_val = agg_df['Total_Count'][0] if not agg_df.empty and pd.notna(agg_df['Total_Count'][0]) else 0
        st.metric(label="Total Transactions", value=f"{int(count_val):,}")
    with col2:
        val = agg_df['Total_Amount'][0] if not agg_df.empty and pd.notna(agg_df['Total_Amount'][0]) else 0
        st.metric(label="Total Transaction Value", value=f"₹ {val:,.2f}")

    st.markdown("---")
    
    # 2. State-wise Map View
    st.subheader("Geographical Transactions Breakdown — State Level")
    map_query = f"SELECT State, SUM(Transaction_amount) as amount FROM Map_transaction WHERE Year={selected_year} AND Quarter={selected_quarter} GROUP BY State"
    map_df = fetch_data(map_query, conn)
    
    if not map_df.empty and india_geojson:
        map_df['Geo_State'] = map_df['State'].map(state_mapping)
        fig = px.choropleth(
            map_df,
            geojson=india_geojson,
            featureidkey='properties.ST_NM',
            locations='Geo_State',
            color='amount',
            color_continuous_scale='Purples',
            title=f'Transaction Value across India ({selected_year} Q{selected_quarter})'
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)

    # 3. Top 10 Districts (across all states)
    st.markdown("---")
    st.subheader("Top 10 Performing Districts")
    top_dist_query = f"SELECT EntityName, SUM(Count) as Total_Count, SUM(Amount) as Total_Amount FROM Top_transaction WHERE EntityType='District' AND Year={selected_year} AND Quarter={selected_quarter} GROUP BY EntityName ORDER BY Total_Amount DESC LIMIT 10"
    top_dist = fetch_data(top_dist_query, conn)
    
    if not top_dist.empty:
        fig2 = px.bar(top_dist, x='Total_Amount', y='EntityName', orientation='h', title='Top 10 Districts by Transaction Value', color='Total_Amount', color_continuous_scale="Purples")
        fig2.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)

    # 4. Transaction Categories
    st.subheader("Transaction Categories")
    cat_query = f"SELECT Transaction_type, SUM(Transaction_amount) as amount FROM Aggregated_transaction WHERE Year={selected_year} AND Quarter={selected_quarter} GROUP BY Transaction_type"
    cat_df = fetch_data(cat_query, conn)
    if not cat_df.empty:
        fig_pie = px.pie(cat_df, values='amount', names='Transaction_type', title='Transaction Amount by Category', hole=0.5, color_discrete_sequence=px.colors.sequential.Purp)
        st.plotly_chart(fig_pie, use_container_width=True)

    # 5. District-wise Breakdown by State
    st.markdown("---")
    st.subheader("District-wise Breakdown by State")

    states_df = fetch_data(f"SELECT DISTINCT State FROM Map_transaction WHERE Year={selected_year} AND Quarter={selected_quarter} ORDER BY State", conn)
    if not states_df.empty:
        state_display_names = sorted([state_mapping.get(s, s) for s in states_df['State'].tolist()])
        selected_display_state = st.selectbox("Select a State to view District breakdown", state_display_names, key="txn_state")
        selected_slug = reverse_state_mapping.get(selected_display_state, selected_display_state)

        dist_query = f"""
            SELECT District, SUM(Transaction_count) as Total_Count, SUM(Transaction_amount) as Total_Amount
            FROM Map_transaction
            WHERE Year={selected_year} AND Quarter={selected_quarter} AND State='{selected_slug}'
            GROUP BY District ORDER BY Total_Amount DESC
        """
        dist_df = fetch_data(dist_query, conn)

        if not dist_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Districts Covered", len(dist_df))
            with col2:
                st.metric("Top District", dist_df['District'].iloc[0])

            fig_dist = px.bar(
                dist_df, x='District', y='Total_Amount',
                title=f'District-wise Transaction Amount — {selected_display_state} ({selected_year} Q{selected_quarter})',
                color='Total_Amount', color_continuous_scale='Purples'
            )
            fig_dist.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_dist, use_container_width=True)

            fig_dist2 = px.bar(
                dist_df, x='District', y='Total_Count',
                title=f'District-wise Transaction Count — {selected_display_state} ({selected_year} Q{selected_quarter})',
                color='Total_Count', color_continuous_scale='Purples'
            )
            fig_dist2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_dist2, use_container_width=True)
        else:
            st.info("No district data available for the selected state and period.")

# ── USERS ─────────────────────────────────────────────────────────────────────
elif domain == "Users":
    # 1. Total Metrics
    agg_query = f"SELECT SUM(Registered_users) as Total_Users, SUM(App_opens) as Total_Opens FROM Map_user WHERE Year={selected_year} AND Quarter={selected_quarter}"
    agg_df = fetch_data(agg_query, conn)
    
    col1, col2 = st.columns(2)
    with col1:
        u_val = agg_df['Total_Users'][0] if not agg_df.empty and pd.notna(agg_df['Total_Users'][0]) else 0
        st.metric(label="Total Registered Users", value=f"{int(u_val):,}")
    with col2:
        o_val = agg_df['Total_Opens'][0] if not agg_df.empty and pd.notna(agg_df['Total_Opens'][0]) else 0
        st.metric(label="Total App Opens", value=f"{int(o_val):,}")

    st.markdown("---")

    # 2. State-wise Map View
    st.subheader("Geographical User Distribution — State Level")
    map_query = f"SELECT State, SUM(Registered_users) as users FROM Map_user WHERE Year={selected_year} AND Quarter={selected_quarter} GROUP BY State"
    map_df = fetch_data(map_query, conn)
    
    if not map_df.empty and india_geojson:
        map_df['Geo_State'] = map_df['State'].map(state_mapping)
        fig = px.choropleth(
            map_df,
            geojson=india_geojson,
            featureidkey='properties.ST_NM',
            locations='Geo_State',
            color='users',
            color_continuous_scale='Blues',
            title=f'Registered Users across India ({selected_year} Q{selected_quarter})'
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)

    # 3. Top Device Brands
    st.markdown("---")
    st.subheader("Top Device Brands")
    brands_query = f"SELECT Brand, SUM(Count) as Total_Count FROM Aggregated_user WHERE Year={selected_year} AND Quarter={selected_quarter} GROUP BY Brand ORDER BY Total_Count DESC LIMIT 10"
    brands_df = fetch_data(brands_query, conn)
    
    if not brands_df.empty:
        fig_brand = px.bar(brands_df, x='Brand', y='Total_Count', title='Top Brands used by Users', color='Total_Count', color_continuous_scale="Blues")
        st.plotly_chart(fig_brand, use_container_width=True)

    # 4. District-wise Breakdown by State
    st.markdown("---")
    st.subheader("District-wise User Breakdown by State")

    states_df_u = fetch_data(f"SELECT DISTINCT State FROM Map_user WHERE Year={selected_year} AND Quarter={selected_quarter} ORDER BY State", conn)
    if not states_df_u.empty:
        state_display_names_u = sorted([state_mapping.get(s, s) for s in states_df_u['State'].tolist()])
        selected_display_state_u = st.selectbox("Select a State to view District breakdown", state_display_names_u, key="usr_state")
        selected_slug_u = reverse_state_mapping.get(selected_display_state_u, selected_display_state_u)

        dist_query_u = f"""
            SELECT District, SUM(Registered_users) as Total_Users, SUM(App_opens) as Total_Opens
            FROM Map_user
            WHERE Year={selected_year} AND Quarter={selected_quarter} AND State='{selected_slug_u}'
            GROUP BY District ORDER BY Total_Users DESC
        """
        dist_df_u = fetch_data(dist_query_u, conn)

        if not dist_df_u.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Districts Covered", len(dist_df_u))
            with col2:
                st.metric("Top District", dist_df_u['District'].iloc[0])

            fig_dist_u = px.bar(
                dist_df_u, x='District', y='Total_Users',
                title=f'District-wise Registered Users — {selected_display_state_u} ({selected_year} Q{selected_quarter})',
                color='Total_Users', color_continuous_scale='Blues'
            )
            fig_dist_u.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_dist_u, use_container_width=True)

            fig_dist_u2 = px.bar(
                dist_df_u, x='District', y='Total_Opens',
                title=f'District-wise App Opens — {selected_display_state_u} ({selected_year} Q{selected_quarter})',
                color='Total_Opens', color_continuous_scale='Blues'
            )
            fig_dist_u2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_dist_u2, use_container_width=True)
        else:
            st.info("No district data available for the selected state and period.")

# ── INSURANCE ─────────────────────────────────────────────────────────────────
elif domain == "Insurance":
    # 1. Total Metrics
    agg_query = f"SELECT SUM(Insurance_count) as Total_Count, SUM(Insurance_amount) as Total_Amount FROM Aggregated_insurance WHERE Year={selected_year} AND Quarter={selected_quarter}"
    agg_df = fetch_data(agg_query, conn)
    
    col1, col2 = st.columns(2)
    with col1:
        count_val = agg_df['Total_Count'][0] if not agg_df.empty and pd.notna(agg_df['Total_Count'][0]) else 0
        st.metric(label="Total Insurance Policies", value=f"{int(count_val):,}")
    with col2:
        val = agg_df['Total_Amount'][0] if not agg_df.empty and pd.notna(agg_df['Total_Amount'][0]) else 0
        st.metric(label="Total Insurance Value", value=f"₹ {val:,.2f}")

    st.markdown("---")

    # 2. State-wise Map View
    st.subheader("Geographical Insurance Breakdown — State Level")
    map_query = f"SELECT State, SUM(Insurance_amount) as amount FROM Map_insurance WHERE Year={selected_year} AND Quarter={selected_quarter} GROUP BY State"
    map_df = fetch_data(map_query, conn)
    
    if not map_df.empty and india_geojson:
        map_df['Geo_State'] = map_df['State'].map(state_mapping)
        fig = px.choropleth(
            map_df,
            geojson=india_geojson,
            featureidkey='properties.ST_NM',
            locations='Geo_State',
            color='amount',
            color_continuous_scale='Greens',
            title=f'Insurance Value across India ({selected_year} Q{selected_quarter})'
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)

    # 3. Top 10 Districts (across all states)
    st.markdown("---")
    st.subheader("Top 10 Districts for Insurance")
    top_dist_query = f"SELECT EntityName, SUM(Count) as Total_Count, SUM(Amount) as Total_Amount FROM Top_insurance WHERE EntityType='District' AND Year={selected_year} AND Quarter={selected_quarter} GROUP BY EntityName ORDER BY Total_Amount DESC LIMIT 10"
    top_dist = fetch_data(top_dist_query, conn)
    
    if not top_dist.empty:
        fig2 = px.bar(top_dist, x='Total_Amount', y='EntityName', orientation='h', title='Top 10 Districts by Insurance Value', color='Total_Amount', color_continuous_scale="Greens")
        fig2.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)

    # 4. District-wise Breakdown by State
    st.markdown("---")
    st.subheader("District-wise Insurance Breakdown by State")

    states_df_i = fetch_data(f"SELECT DISTINCT State FROM Map_insurance WHERE Year={selected_year} AND Quarter={selected_quarter} ORDER BY State", conn)
    if not states_df_i.empty:
        state_display_names_i = sorted([state_mapping.get(s, s) for s in states_df_i['State'].tolist()])
        selected_display_state_i = st.selectbox("Select a State to view District breakdown", state_display_names_i, key="ins_state")
        selected_slug_i = reverse_state_mapping.get(selected_display_state_i, selected_display_state_i)

        dist_query_i = f"""
            SELECT District, SUM(Insurance_count) as Total_Count, SUM(Insurance_amount) as Total_Amount
            FROM Map_insurance
            WHERE Year={selected_year} AND Quarter={selected_quarter} AND State='{selected_slug_i}'
            GROUP BY District ORDER BY Total_Amount DESC
        """
        dist_df_i = fetch_data(dist_query_i, conn)

        if not dist_df_i.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Districts Covered", len(dist_df_i))
            with col2:
                st.metric("Top District", dist_df_i['District'].iloc[0])

            fig_dist_i = px.bar(
                dist_df_i, x='District', y='Total_Amount',
                title=f'District-wise Insurance Value — {selected_display_state_i} ({selected_year} Q{selected_quarter})',
                color='Total_Amount', color_continuous_scale='Greens'
            )
            fig_dist_i.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_dist_i, use_container_width=True)

            fig_dist_i2 = px.bar(
                dist_df_i, x='District', y='Total_Count',
                title=f'District-wise Insurance Policy Count — {selected_display_state_i} ({selected_year} Q{selected_quarter})',
                color='Total_Count', color_continuous_scale='Greens'
            )
            fig_dist_i2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_dist_i2, use_container_width=True)
        else:
            st.info("No district data available for the selected state and period.")