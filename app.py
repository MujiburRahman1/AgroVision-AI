import streamlit as st
import pandas as pd
import requests
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
    """Simulates FAOSTAT API call with realistic parameters"""
    try:
        # Generate realistic sample data
        years = list(range(start_year, end_year + 1))
        base_value = {
            "Production": 1000000,
            "Yield": 30,
            "Area Harvested": 50000,
            "Import Quantity": 500000,
            "Export Quantity": 300000,
            "Value": 250000000,
            "Food Supply": 2500,
            "Dietary Energy Supply": 3000,
            "Producer Price": 150,
            "Consumer Price": 200,
            "Emissions": 50000,
            "Carbon Stock": 1000000
        }.get(metric, 1000)
        
        # Create realistic trends
        data = {
            "Year": years,
            "Value": [int(base_value * (1 + 0.02*(year - start_year)) * (0.95 + 0.1*(item_code%10)/10)) 
                     for year in years],
            "Unit": {
                "Production": "tonnes",
                "Yield": "hg/ha",
                "Area Harvested": "ha",
                "Import Quantity": "tonnes",
                "Export Quantity": "tonnes",
                "Value": "1000 US$",
                "Food Supply": "kcal/capita/day",
                "Dietary Energy Supply": "kcal/capita/day",
                "Producer Price": "US$/tonne",
                "Consumer Price": "US$/tonne",
                "Emissions": "kt CO2eq",
                "Carbon Stock": "kt C"
            }.get(metric, "units"),
            "Flag": ["Official" if year%2==0 else "Estimated" for year in years],
            "Country": selected_country,
            "Item": selected_commodity,
            "Domain": selected_domain,
            "Metric": metric
        }
        
        df = pd.DataFrame(data)
        return df
    
    except Exception as e:
        st.error(f"Error generating data: {str(e)}")
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
# UPLOADED DATASET AI ANALYSIS
# ==============================================

st.markdown("---")
st.header("📁 Uploaded FAOSTAT Dataset Analysis")
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    upload_df = pd.read_csv(uploaded_file)
    st.caption(f"Rows: {len(upload_df):,} | Columns: {len(upload_df.columns)}")
    st.dataframe(upload_df.head(20), use_container_width=True)

    def pick_column(columns, candidates):
        for name in candidates:
            if name in columns:
                return name
        return None

    year_col = pick_column(upload_df.columns, ["Year", "year", "YEAR"])
    value_col = pick_column(upload_df.columns, ["Value", "value", "VALUE"])

    st.subheader("Automatic Data Summary")
    numeric_cols = upload_df.select_dtypes(include="number").columns.tolist()
    st.markdown(
        f"- Total rows: {len(upload_df):,}\n"
        f"- Total columns: {len(upload_df.columns)}\n"
        f"- Numeric columns: {len(numeric_cols)}"
    )
    if numeric_cols:
        summary_stats = upload_df[numeric_cols].describe().T
        st.dataframe(
            summary_stats.style.format("{:,.2f}"),
            use_container_width=True
        )
    else:
        st.warning("No numeric columns detected for summary statistics.")

    st.subheader("Trend Analysis")
    trend_group = None
    change_pct = None
    volatility = None
    if year_col and value_col:
        trend_df = upload_df[[year_col, value_col]].copy()
        trend_df[year_col] = pd.to_numeric(trend_df[year_col], errors="coerce")
        trend_df[value_col] = pd.to_numeric(trend_df[value_col], errors="coerce")
        trend_df = trend_df.dropna()

        if not trend_df.empty:
            trend_group = (
                trend_df.groupby(year_col, as_index=False)[value_col]
                .sum()
                .sort_values(year_col)
            )
            first_value = trend_group.iloc[0][value_col]
            last_value = trend_group.iloc[-1][value_col]
            if first_value != 0:
                change_pct = ((last_value - first_value) / first_value) * 100
            volatility = trend_group[value_col].pct_change().std() * 100

            trend_direction = "increasing" if last_value >= first_value else "decreasing"
            st.markdown(
                f"- Trend is **{trend_direction}** from {int(trend_group.iloc[0][year_col])} "
                f"to {int(trend_group.iloc[-1][year_col])}."
            )
            if change_pct is not None:
                st.markdown(f"- Overall change: **{change_pct:.1f}%**.")
            if volatility is not None and pd.notna(volatility):
                st.markdown(f"- Volatility (std of YoY %): **{volatility:.2f}%**.")

            fig, ax = plt.subplots(figsize=(10, 4))
            sns.lineplot(
                data=trend_group,
                x=year_col,
                y=value_col,
                marker="o",
                ax=ax
            )
            ax.set_title("Trend Over Time")
            ax.set_xlabel("Year")
            ax.set_ylabel("Value")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("Year/Value columns found but contain no usable numeric data.")
    else:
        st.warning("Year/Value columns not found. Trend analysis skipped.")

    st.subheader("Policy Recommendations")
    recommendations = []
    if change_pct is not None:
        if change_pct > 5:
            recommendations.append("Sustain growth by investing in productivity and market access.")
        elif change_pct < -5:
            recommendations.append("Investigate drivers of decline and apply targeted support or reforms.")
        else:
            recommendations.append("Stabilize the sector with incremental improvements and risk monitoring.")
    else:
        recommendations.append("Improve data coverage to enable trend-based decision-making.")

    if volatility is not None and pd.notna(volatility):
        if volatility > 20:
            recommendations.append("High volatility suggests need for buffers, insurance, or price stabilization.")
        elif volatility < 5:
            recommendations.append("Low volatility indicates stable conditions; focus on efficiency gains.")

    for rec in recommendations:
        st.markdown(f"- {rec}")

    st.subheader("Natural Language Q&A")
    question = st.text_input("Ask a question about the dataset")
    if question:
        q = question.lower()
        answer = "I can summarize totals, averages, min/max, or trend if Year/Value exist."
        if value_col:
            value_series = pd.to_numeric(upload_df[value_col], errors="coerce")
            if "average" in q or "mean" in q:
                answer = f"Average {value_col}: {value_series.mean():,.2f}"
            elif "total" in q or "sum" in q:
                answer = f"Total {value_col}: {value_series.sum():,.2f}"
            elif "max" in q or "highest" in q:
                answer = f"Max {value_col}: {value_series.max():,.2f}"
            elif "min" in q or "lowest" in q:
                answer = f"Min {value_col}: {value_series.min():,.2f}"

        if "trend" in q and trend_group is not None:
            direction = "increasing" if change_pct is None or change_pct >= 0 else "decreasing"
            answer = f"Overall trend is {direction} with change of {change_pct:.1f}%."

        if "year" in q and year_col:
            year_series = pd.to_numeric(upload_df[year_col], errors="coerce")
            if "latest" in q or "max" in q:
                answer = f"Latest year in data: {int(year_series.max())}"
            elif "earliest" in q or "min" in q:
                answer = f"Earliest year in data: {int(year_series.min())}"

        st.info(answer)

    st.subheader("Report")
    st.markdown("**Summary**")
    st.markdown(
        f"- Rows: {len(upload_df):,}\n"
        f"- Columns: {len(upload_df.columns)}\n"
        f"- Numeric columns: {len(numeric_cols)}"
    )
    st.markdown("**Trends**")
    if trend_group is not None and change_pct is not None:
        st.markdown(f"- Change from first to last year: {change_pct:.1f}%")
    else:
        st.markdown("- Trend analysis not available for this dataset.")
    st.markdown("**Recommendations**")
    for rec in recommendations:
        st.markdown(f"- {rec}")

# ==============================================
# FOOTER
# ==============================================

st.markdown("---")
st.sidebar.caption(
    "This web app is a prototype and not affiliated with FAOSTAT. Data is simulated for demonstration purposes."
)
