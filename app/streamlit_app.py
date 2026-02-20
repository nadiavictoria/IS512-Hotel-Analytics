import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Hotel 360 Analytics", layout="wide")

# --- DATA LOADER ---
@st.cache_data
def load_data(query, params=None):
    # Adjust path to your DB
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'reviews_analysis.db')
    conn = sqlite3.connect(db_path)
    if params:
        df = pd.read_sql(query, conn, params=params)
    else:
        df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- SIDEBAR: FILTERS ---
st.sidebar.title("🏨 Dashboard Controls")

# Load Hotel List (Sorted Ascending)
# Added 'ORDER BY hotel_id ASC' so the dropdown is easy to navigate
hotels_df = load_data("""
    SELECT hotel_id, hotel_id as name 
    FROM hotels 
    ORDER BY hotel_id ASC
""") 

selected_hotel = st.sidebar.selectbox("Select Hotel", hotels_df['name'])

# --- MAIN DATA FETCHING ---
# 1. Fetch Reviews
query_reviews = """
    SELECT * FROM reviews 
    WHERE hotel_id = ? 
    ORDER BY date_stayed DESC
"""
df_reviews = load_data(query_reviews, params=(selected_hotel,))
df_reviews['date_stayed'] = pd.to_datetime(df_reviews['date_stayed'])
df_reviews['review_date'] = pd.to_datetime(df_reviews['review_date'])

# 2. Fetch Benchmarks
query_benchmark = """
    SELECT 
        AVG(avg_service_rating) as Service,
        AVG(avg_cleanliness_rating) as Cleanliness,
        AVG(avg_value_rating) as Value,
        AVG(avg_location_rating) as Location,
        AVG(avg_sleep_quality_rating) as Sleep,
        AVG(avg_rooms_rating) as Rooms
    FROM hotels
"""
df_benchmark = load_data(query_benchmark)

# --- PRE-CALCULATE RATINGS FOR TAB 1 ---
categories = ['service_rating', 'cleanliness_rating', 'value_rating', 
              'location_rating', 'sleep_quality_rating', 'rooms_rating']
cat_names = [c.replace('_rating', '').title() for c in categories]
hotel_means = df_reviews[categories].mean().tolist()

# --- APP TITLE ---
st.title(f"Analytics for: {selected_hotel}")

# Reduced to 3 Tabs now
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "💬 Customer Voice", "🏆 Benchmarking"])

# ==========================================
# TAB 1: EXECUTIVE SUMMARY
# ==========================================
with tab1:
    # --- ROW 1: KPIs ---
    st.markdown("### High Level Performance")
    
    current_rating = df_reviews['overall_rating'].mean()
    total_reviews = len(df_reviews)
    happy_guests = len(df_reviews[df_reviews['overall_rating'] >= 4])
    satisfaction_rate = (happy_guests / total_reviews) * 100 if total_reviews > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Rating", f"{current_rating:.2f}/5.0")
    col2.metric("Total Reviews", f"{total_reviews}")
    col3.metric("Customer Satisfaction", f"{satisfaction_rate:.1f}%")

    st.markdown("---")

    # --- ROW 2: TRENDS & QUALITY SNAPSHOT ---
    left_col, right_col = st.columns([1.5, 1])

    with left_col:
        st.subheader("Rating Trend")
        
        # 1. Sort by date to ensure the line chart flows correctly
        df_sorted = df_reviews.sort_values('date_stayed')
        
        # 2. Resample by Month ('ME') and calculate Mean AND Count
        # This proves we are using ALL data, just grouping it
        df_trend = df_sorted.set_index('date_stayed').resample('ME')['overall_rating'].agg(['mean', 'count']).reset_index()
        
        # Rename columns for cleaner tooltips
        df_trend.columns = ['date_stayed', 'Average Rating', 'Review Count']
        
        # 3. Plot with Hover Data
        fig_trend = px.line(
            df_trend, 
            x='date_stayed', 
            y='Average Rating', 
            markers=True,
            # Add 'Review Count' to the hover tooltip so you can see the volume of data
            hover_data=['Review Count'],
            title="Monthly Average Rating"
        )
        
        fig_trend.update_layout(yaxis_range=[1, 5], height=400)
        st.plotly_chart(fig_trend, use_container_width=True)

    with right_col:
        st.subheader("Quality Breakdown")
        
        # 1. Radar Chart
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=hotel_means,
            theta=cat_names,
            fill='toself',
            name='Current Performance'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])), 
            showlegend=False,
            height=300,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # 2. Logic-Based Insights
        st.markdown("#### Operational Insights")
        
        critical_areas = []
        improvement_areas = []
        
        for name, score in zip(cat_names, hotel_means):
            if score < 2.5:
                critical_areas.append(f"{name} ({score:.2f})")
            elif score < 4.0:
                improvement_areas.append(f"{name} ({score:.2f})")
        
        if critical_areas:
            st.error("🚨 **Critical Focus Area (Score < 2.5)**")
            for item in critical_areas:
                st.write(f"- {item}")
        
        if improvement_areas:
            st.warning("⚠️ **Improvement Area (Score 2.5 - 4.0)**")
            for item in improvement_areas:
                st.write(f"- {item}")
        
        if not critical_areas and not improvement_areas:
            st.success("🎉 **Your hotel is doing well!**")
            st.caption("All operational categories are rated above 4.0.")

# ==========================================
# TAB 2: CUSTOMER VOICE
# ==========================================
with tab2:
    st.markdown("### What are guests saying?")
    
    filter_sentiment = st.radio("Filter Reviews:", ["All", "Positive (4-5★)", "Negative (1-2★)"], horizontal=True)
    
    if filter_sentiment == "Positive (4-5★)":
        view_df = df_reviews[df_reviews['overall_rating'] >= 4]
    elif filter_sentiment == "Negative (1-2★)":
        view_df = df_reviews[df_reviews['overall_rating'] <= 2]
    else:
        view_df = df_reviews

    # Display the dataframe
    st.dataframe(
        view_df[['date_stayed', 'overall_rating', 'title', 'text']], # Removed .head(10) to show everything
        column_config={
            "date_stayed": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
            "overall_rating": st.column_config.NumberColumn("Stars", format="%.0f ⭐"),
            "title": "Title",
            "text": "Review"
        },
        use_container_width=True,
        hide_index=True,
        height=600 # Sets a fixed height with a scrollbar
    )

# ==========================================
# TAB 3: BENCHMARKING
# ==========================================
with tab3:
    st.markdown("### Competitive Positioning")

    # --- 1. CLUSTER ANALYSIS ---
    # Fetch the cluster for the selected hotel
    query_cluster = "SELECT kmeans_cluster, PCA1, PCA2 FROM hotels WHERE hotel_id = ?"
    df_cluster_info = load_data(query_cluster, params=(selected_hotel,))
    
    # Define Cluster Labels map
    cluster_labels = {
        0: "0: Top of the Line",
        1: "1: Convenient",
        2: "2: Below Average",
        3: "3: Terrible",
        4: "4: Good, but Inconvenient"
    }

    if not df_cluster_info.empty:
        cluster_id = int(df_cluster_info.iloc[0]['kmeans_cluster'])
        
        cluster_info = {
            0: {"desc": "Best hotels, above average in every category.", "action": "✨ Keep doing what you're doing."},
            1: {"desc": "No-frills, location-focused hotels.", "action": "📍 Market your convenience and transport links."},
            2: {"desc": "Below average ratings across the board.", "action": "🔧 Fix service/room basics before worrying about location."},
            3: {"desc": "Worst hotels, critical failures in service/rooms.", "action": "🚨 Immediate management reorganization required."},
            4: {"desc": "Great hotels in remote locations.", "action": "🚌 Offer free shuttles to offset location disadvantage."}
        }
        
        info = cluster_info.get(cluster_id, {"desc": "Unknown", "action": ""})

        # Display Text Insight
        st.info(f"**Group {cluster_labels.get(cluster_id, f'Cluster {cluster_id}')}**")
        st.markdown(f"**Insight:** {info['desc']}")
        st.markdown(f"**Strategy:** {info['action']}")

    st.markdown("---")

    # --- 2. CLUSTER VISUALIZATION ---
    st.subheader("Cluster Map")
    st.caption("Where does your hotel sit in the market landscape? (Based on PCA reduction of key rating metrics)")

    # A. Fetch All Hotels Data for the background plot
    query_all_pca = "SELECT hotel_id, kmeans_cluster, PCA1, PCA2 FROM hotels"
    df_pca = load_data(query_all_pca)
    
    # Map cluster IDs to friendly names
    df_pca['Cluster Name'] = df_pca['kmeans_cluster'].map(cluster_labels)
    df_pca = df_pca.sort_values('kmeans_cluster')

    # B. Create the Base Scatter Plot (All Hotels)
    fig_pca = px.scatter(
        df_pca, 
        x='PCA1', 
        y='PCA2', 
        color='Cluster Name',
        hover_data=['hotel_id'],
        color_discrete_map={
            "0: Top of the Line": "#2ecc71",   # Green
            "1: Convenient": "#f1c40f",        # Yellow
            "2: Below Average": "#e67e22",     # Orange
            "3: Terrible": "#e74c3c",          # Red
            "4: Good, but Inconvenient": "#3498db" # Blue
        },
        opacity=0.4
    )

    # C. Calculate and Plot Centroids (The 'X' marks)
    centroids = df_pca.groupby('Cluster Name')[['PCA1', 'PCA2']].mean().reset_index()
    fig_pca.add_trace(go.Scatter(
        x=centroids['PCA1'], 
        y=centroids['PCA2'],
        mode='markers',
        marker=dict(symbol='x', size=15, color='white', line=dict(width=2)),
        name='Centroids',
        hoverinfo='skip'
    ))

    # D. Highlight Selected Hotel
    if not df_cluster_info.empty:
        my_pca1 = df_cluster_info.iloc[0]['PCA1']
        my_pca2 = df_cluster_info.iloc[0]['PCA2']
        
        fig_pca.add_trace(go.Scatter(
            x=[my_pca1], 
            y=[my_pca2],
            mode='markers+text',
            marker=dict(symbol='star', size=25, color='red', line=dict(width=2, color='white')),
            name='YOU ARE HERE',
            text=["📍 YOU"],
            textposition="top center"
        ))

    fig_pca.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig_pca, use_container_width=True)

    st.markdown("---")

    
    # --- 3. MARKET POSITION ---
    # Prepare Data
    market_means = df_benchmark.iloc[0].tolist()
    
    # Calculate gaps
    gaps = {}
    for cat, my_score, mkt_score in zip(cat_names, hotel_means, market_means):
        gaps[cat] = my_score - mkt_score

    best_cat = max(gaps, key=gaps.get)
    best_gap = gaps[best_cat]
    
    worst_cat = min(gaps, key=gaps.get)
    worst_gap = gaps[worst_cat]

    st.subheader("Market Comparison")
    
    col1, col2 = st.columns(2)

    # SCENARIO 1: Mixed Bag
    if best_gap > 0 and worst_gap < 0:
        with col1:
            st.success(f"🏆 **Selling Point**")
            st.metric(label=best_cat, value=f"{hotel_means[cat_names.index(best_cat)]:.2f}", delta=f"+{best_gap:.2f} above market")
        with col2:
            st.error(f"⚠️ **Weakness**")
            st.metric(label=worst_cat, value=f"{hotel_means[cat_names.index(worst_cat)]:.2f}", delta=f"{worst_gap:.2f} below market")

    # SCENARIO 2: Market Leader
    elif best_gap > 0 and worst_gap >= 0:
        st.balloons()
        st.success("🌟 **Market Leader Status**")
        st.write("You are outperforming the market average in **ALL** categories.")
        col1.metric(label=f"Top Competitive Advantage: {best_cat}", value=f"{hotel_means[cat_names.index(best_cat)]:.2f}", delta=f"+{best_gap:.2f} lead")

    # SCENARIO 3: Underperformer
    elif best_gap <= 0 and worst_gap < 0:
        st.error("📉 **Market Lag**")
        st.write("You are currently trailing the market average in all categories.")
        col1.metric(label=f"Critical Priority: {worst_cat}", value=f"{hotel_means[cat_names.index(worst_cat)]:.2f}", delta=f"{worst_gap:.2f} gap")

    # --- 3. CHART ---
    st.markdown("#### Rating Comparison Breakdown")
    
    fig_bar = go.Figure(data=[
        go.Bar(name='My Hotel', x=cat_names, y=hotel_means, marker_color='#0068c9'),
        go.Bar(name='Market Avg', x=cat_names, y=market_means, marker_color='#83c9ff')
    ])
    fig_bar.update_layout(barmode='group', height=400)
    st.plotly_chart(fig_bar, use_container_width=True)