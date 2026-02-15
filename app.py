import streamlit as st
import pandas as pd
import faostat
import datetime as dt
import matplotlib.pyplot as plt
import seaborn as sns
import io

# Page config (no forced theme)
st.set_page_config(
    page_title="FAOSTAT Explorer", 
    page_icon="🌾", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title (no forced color)
st.title("🌾 FAOSTAT Agricultural Data Explorer")
st.markdown("Access global agricultural statistics from the UN Food and Agriculture Organization")

# ==============================================
# FAOSTAT DATA CATALOGUE (Simplified)
# ==============================================

DOMAINS = {
    "Production": {"code": "QCL", "metrics": ["Production", "Yield", "Area Harvested"]},
    "Trade": {"code": "TCL", "metrics": ["Import Quantity", "Export Quantity", "Value"]},
    "Food Security": {"code": "FS", "metrics": ["Food Supply", "Dietary Energy Supply"]},
    "Prices": {"code": "PP", "metrics": ["Producer Price", "Consumer Price"]},
    "Emissions": {"code": "GT", "metrics": ["Emissions", "Carbon Stock"]}
}

COMMODITIES = {
    "Crops": {
        "Wheat": 15, "Rice": 27, "Maize": 56, "Soybeans": 236, 
        "Potatoes": 116, "Tomatoes": 388, "Coffee": 656, "Tea": 667,
        "Barley": 78, "Sugarcane": 89, "Cotton": 92, "Bananas": 123,
        "Oranges": 145, "Apples": 167, "Grapes": 189, "Peanuts": 210
    },
    "Livestock": {
        "Beef": 867, "Poultry": 1058, "Milk": 882, "Eggs": 1062,
        "Sheep": 1123, "Goat": 1145, "Pork": 1167, "Fish": 1189,
        "Honey": 1201, "Wool": 1223, "Buffalo": 1245
    }
}
COUNTRIES = {
    "Americas": {
        "USA": 231, "Brazil": 21, "Canada": 39, 
        "Mexico": 142, "Argentina": 10, "Chile": 45, 
        "Colombia": 32, "Peru": 51, "Venezuela": 58
    },
    "Asia": {
        "China": 351, "India": 100, "Pakistan": 165, 
        "Japan": 110, "South Korea": 130, "Indonesia": 101, 
        "Vietnam": 120, "Thailand": 140, "Malaysia": 150
    },
    "Europe": {
        "France": 68, "Germany": 79, "Russia": 185, 
        "Italy": 106, "United Kingdom": 234, "Spain": 210, 
        "Netherlands": 150, "Sweden": 160, "Poland": 170
    },
    "Africa": {
        "Nigeria": 159, "South Africa": 205, 
        "Egypt": 59, "Kenya": 117, "Ethiopia": 62, 
        "Ghana": 45, "Morocco": 78, "Algeria": 89
    },
    "Oceania": {
        "Australia": 36, "New Zealand": 40, 
        "Fiji": 90, "Papua New Guinea": 91, "Samoa": 92
    },
    "Middle East": {
        "Saudi Arabia": 250, "Iran": 260, "Turkey": 270, 
        "Iraq": 280, "Israel": 290, "Jordan": 300
    }
}

# ==============================================
# UI COMPONENTS (no forced color)
# ==============================================

# Sidebar Filters
with st.sidebar:
    st.header("🔍 Filters")
    
    # Domain selection
    selected_domain = st.selectbox(
        "1. Select Domain", 
        list(DOMAINS.keys()),
        index=0
    )
    
    # Metric selection based on domain
    available_metrics = DOMAINS[selected_domain]["metrics"]
    selected_metric = st.selectbox(
        "2. Select Metric", 
        available_metrics,
        index=0
    )
    
    # Commodity type selection
    st.markdown("3. Commodity Type")
    commodity_type = st.radio(
        "",
        list(COMMODITIES.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Commodity selection
    selected_commodity = st.selectbox(
        "4. Select Commodity", 
        list(COMMODITIES[commodity_type].keys()),
        index=0
    )
    
    # Region selection
    region = st.selectbox(
        "5. Select Region", 
        list(COUNTRIES.keys()),
        index=0
    )
    
    # Country selection
    selected_country = st.selectbox(
        "6. Select Country", 
        list(COUNTRIES[region].keys()),
        index=0
    )
    
    # Year range
    st.markdown("7. Year Range")
    year_range = st.slider(
        "",
        1961, dt.datetime.now().year,
        (2000, dt.datetime.now().year-1),
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown(
        """
        **About FAOSTAT**:
        The Food and Agriculture Organization's statistical database covering:
        - 📈 Agricultural production
        - 🌍 Trade flows
        - 🍲 Food security
        - 🌱 Climate impacts
        """
    )

# ==============================================
# DATA FETCHING FUNCTION
# ==============================================

@st.cache_data(ttl=24*3600)
def fetch_faostat_data(domain, metric, item_code, country_code, start_year, end_year):
    """Fetches FAOSTAT data using the faostat package"""
    def get_column(dataframe, *candidates):
        for name in candidates:
            if name in dataframe.columns:
                return dataframe[name]
        return pd.Series([None] * len(dataframe))

    try:
        years = list(range(start_year, end_year + 1))
        try:
            df = faostat.get_data_df(
                domain,
                [country_code],
                [item_code],
                years
            )
        except TypeError:
            df = faostat.get_data_df(
                domain,
                area_codes=[country_code],
                item_codes=[item_code],
                year_codes=years
            )

        if df is None or df.empty:
            st.warning("No data returned for the selected filters.")
            return None

        element_col = None
        for candidate in ["element", "Element"]:
            if candidate in df.columns:
                element_col = candidate
                break

        if element_col:
            df = df[df[element_col].astype(str).str.lower() == metric.lower()]
            if df.empty:
                st.warning("No data returned for the selected metric.")
                return None

        df_out = pd.DataFrame({
            "Year": get_column(df, "year", "Year"),
            "Value": get_column(df, "value", "Value"),
            "Unit": get_column(df, "unit", "Unit"),
            "Country": get_column(df, "area", "Area"),
            "Item": get_column(df, "item", "Item"),
            "Domain": domain,
            "Metric": metric
        })

        df_out["Year"] = pd.to_numeric(df_out["Year"], errors="coerce")
        df_out["Value"] = pd.to_numeric(df_out["Value"], errors="coerce")
        df_out = df_out.sort_values("Year", ascending=True)
        return df_out

    except Exception as e:
        st.error(f"FAOSTAT fetch failed: {str(e)}")
        return None

# ==============================================
# MAIN DISPLAY
# ==============================================

# Fetch button
col1, col2 = st.columns([3, 1])
with col1:
    if st.button("🚀 Fetch Data", use_container_width=True, type="primary"):
        with st.spinner(f"Fetching {selected_metric} data for {selected_commodity} in {selected_country}..."):
            # Get codes
            domain_code = DOMAINS[selected_domain]["code"]
            item_code = COMMODITIES[commodity_type][selected_commodity]
            country_code = COUNTRIES[region][selected_country]
            
            # Fetch data
            df = fetch_faostat_data(
                domain_code,
                selected_metric,
                item_code,
                country_code,
                year_range[0],
                year_range[1]
            )
            
            if df is not None:
                st.session_state.faostat_data = df
                st.session_state.current_query = {
                    "metric": selected_metric,
                    "commodity": selected_commodity,
                    "country": selected_country
                }
                st.success("Data loaded successfully!")

# Display results if data exists
if 'faostat_data' in st.session_state:
    df = st.session_state.faostat_data
    query = st.session_state.current_query
    
    # Metrics cards
    st.markdown("---")
    st.subheader("Key Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "First Year Value", 
            f"{df.iloc[0]['Value']:,} {df.iloc[0]['Unit']}",
            help=f"Value in {year_range[0]}"
        )
    with col2:
        st.metric(
            "Last Year Value", 
            f"{df.iloc[-1]['Value']:,} {df.iloc[-1]['Unit']}",
            help=f"Value in {year_range[1]}"
        )
    with col3:
        change = ((df.iloc[-1]['Value'] - df.iloc[0]['Value']) / df.iloc[0]['Value']) * 100
        st.metric(
            "Change Over Period", 
            f"{change:.1f}%",
            delta_color="inverse" if change < 0 else "normal",
            help=f"Percentage change from {year_range[0]} to {year_range[1]}"
        )
    
    # Main dataframe
    st.markdown("---")
    st.subheader(f"{query['metric']} of {query['commodity']} in {query['country']}")
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        height=min(400, 35 * (len(df) + 1))
    )
    
    # Visualization tabs
    st.markdown("---")
    tab1, tab2 = st.tabs(["📈 Time Series Analysis", "📊 Statistical Insights"])
    
    with tab1:
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Create plot
        sns.lineplot(
            data=df, 
            x="Year", 
            y="Value", 
            marker="o",
            color="blue",
            linewidth=2.5,
            markersize=8
        )
        
        # Customize plot appearance
        ax.set_title(
            f"{query['metric']} Trend ({query['country']})",
            pad=20,
            fontsize=14
        )
        ax.set_xlabel("Year")
        ax.set_ylabel(
            f"{query['metric']} ({df.iloc[0]['Unit']})"
        )
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        st.pyplot(fig)
        
        # Save chart to buffer for download
        chart_buffer = io.BytesIO()
        fig.savefig(chart_buffer, format='png', bbox_inches='tight')
        chart_buffer.seek(0)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Descriptive Statistics")
            stats_df = df["Value"].describe().to_frame().T
            st.dataframe(
                stats_df.style.format("{:,.2f}"),
                use_container_width=True
            )
        
        with col2:
            st.subheader("Annual Changes")
            df["YoY Change"] = df["Value"].pct_change() * 100
            yoy_df = df[["Year", "YoY Change"]].dropna()
            st.dataframe(
                yoy_df.style.format({"YoY Change": "{:+.2f}%"}),
                use_container_width=True,
                height=min(400, 35 * (len(yoy_df) + 1))
            )
    
    # Export options
    st.markdown("---")
    st.subheader("Export Data")
    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "💾 Download CSV",
            csv,
            file_name=f"FAOSTAT_{query['commodity']}_{query['country']}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col2:
        st.download_button(
            "📊 Download Chart as PNG",
            chart_buffer,
            file_name="FAOSTAT_chart.png",
            mime="image/png",
            use_container_width=True
        )

# ==============================================
# FOOTER
# ==============================================

st.markdown("---")
st.sidebar.caption(
    "This web app is a prototype and not affiliated with FAOSTAT. Data is simulated for demonstration purposes."
)
