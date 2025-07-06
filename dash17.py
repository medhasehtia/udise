import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json

# ─── Page Setup & Styling ─────────────────────────────────────────────────────
st.set_page_config(page_title="UDISE+ Infrastructure Dashboard", layout="wide")
# st.title("UDISE+ Infrastructure Dashboard")
# st.markdown("""
#     <style>
#     @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600&family=Source+Sans+Pro:wght@400&display=swap');
#     html, body, [class*="css"] { font-family: 'Source Sans Pro', sans-serif !important; }
#     h1, h2, h3, h4 { font-family: 'Montserrat', sans-serif !important; }
#     .metric-container .metric-value { color: #0C4DA2 !important; }
#     </style>
# """, unsafe_allow_html=True)
st.markdown(
    "<h1 style='margin-bottom:10px;'>UDISE+ Infrastructure Dashboard</h1>",
    unsafe_allow_html=True
)

#PRIMARY, SECONDARY, ACCENT = "#0C4DA2", "#10BB51", "#F1AB0A"

PRIMARY   = "#5D3FD3"   # a rich indigo
SECONDARY = "#FF6B6B"   # a vibrant coral-red
ACCENT    = "#4ECDC4"   # a fresh mint-green


# ─── Load & Prepare Data ─────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # 1. Read the raw CSVs
    #prof = pd.read_csv("data/100_prof1.csv")     # profile data
    prof = pd.read_csv("data/100_prof1.csv")
    #fac  = pd.read_csv("data/100_prof1.csv")    # facility data
    fac = pd.read_csv("data/100_fac.csv")


    # 2. Rename profile columns that don’t match our variables
    prof = prof.rename(columns={
        "managment":              "management",
        "rural_urban":            "location",
        "school_category":        "category",
        "minority_school":        "minority",
        "resi_school":            "residential",
        "special_school_for_cwsn":"special_cwsn"
    })

    # 3. Rename facility columns that don’t match our variables
    fac = fac.rename(columns={
        "availability_ramps":        "ramps",
        "availability_of_handrails": "handrails",
        "comp_ict_lab_yn":           "ict_lab"
    })

    # 4. Merge on the common key
    df = prof.merge(fac, on="pseudocode", how="inner")

    # 5. Feature‐engineering core flags & indices
    df["func_electricity"]      = df["electricity_availability"] == 1
    df["func_water"]            = df["tap_fun_yn"] == 1
    df["func_handwash"]         = df["handwash_facility_for_meal"] == 1
    df["playground"]            = df["playground_available"] == 1
    df["library"]               = df["library_availability"] == 1
    df["internet"]              = df["internet"] == 1
    df["ramps"]                 = df["ramps"] == 1
    df["handrails"]             = df["handrails"] == 1
    df["pct_toilet_func_girls"] = (
        df["total_girls_func_toilet"] / df["total_girls_toilet"]
    )
    df["computer_yn"] = np.where(df["desktop"] > 0, 1, 0)

    binary_cols = [
    "func_electricity",
    "func_water",
    "pct_toilet_func_girls",
    "func_handwash",
    "ramps",
    "handrails",
    "internet",
    "ict_lab"

    ]

    for col in binary_cols:
        df[col] = (df[col] == 1).astype(int)

    df["infra_index"] = df[
        ["func_electricity","func_water","pct_toilet_func_girls","func_handwash"]
    ].mean(axis=1)

    df["equity_index"] = df[
        ["ramps","handrails","pct_toilet_func_girls"]
    ].mean(axis=1)

    # 6. Decode all the code‐variables into human labels
    df["location"]     = df["location"].map({1:"Rural",2:"Urban"})
    df["management"]   = df["management"].map({1:"Government",2:"Government Aided",3:"Private"})
    df["category"]     = df["category"].map({1:"Primary",2:"Upper Primary",3:"Secondary",4:"Higher Secondary"})
    df["minority"]     = df["minority"].map({1:"Yes",2:"No"})
    df["residential"]  = df["residential"].map({1:"Completely",2:"Partially",3:"Non-residential"})
    df["special_cwsn"] = df["special_cwsn"].map({1:"Yes",2:"No"})

    return df

df = load_data()

# ─── Sidebar Filters ─────────────────────────────────────────────────────────
st.sidebar.header("Filters")
state_sel    = st.sidebar.multiselect("State",  sorted(df.state.unique()), default=sorted(df.state.unique()))
district_sel = st.sidebar.multiselect("District", sorted(df[df.state.isin(state_sel)].district.unique()))
loc_sel      = st.sidebar.multiselect("Location", ["Rural","Urban"], default=["Rural","Urban"])
mgmt_sel     = st.sidebar.multiselect("Management", ["Government","Government Aided","Private"], default=["Government","Government Aided","Private"])
cat_sel      = st.sidebar.multiselect("Category", ["Primary","Upper Primary","Secondary","Higher Secondary"], default=["Primary","Upper Primary","Secondary","Higher Secondary"])
minority_sel = st.sidebar.multiselect("Minority-managed", ["Yes","No"], default=["Yes","No"])
resi_sel     = st.sidebar.multiselect("Residential", ["Completely","Partially","Non-residential"], default=["Completely","Partially","Non-residential"])
cwsn_sel     = st.sidebar.multiselect("CWSN-only", ["Yes","No"], default=["Yes","No"])

mask = (
    df.state.isin(state_sel) &
    (df.district.isin(district_sel) if district_sel else True) &
    df.location.isin(loc_sel) &
    df.management.isin(mgmt_sel) &
    df.category.isin(cat_sel) &
    df.minority.isin(minority_sel) &
    df.residential.isin(resi_sel) &
    df.special_cwsn.isin(cwsn_sel)
)

df_filt = df[mask] 

# ─── Tabs Setup ───────────────────────────────────────────────────────────────
tabs = st.tabs([
    "WASH+ Infrastructure",
    "Equity & Accessibility",
    "Digital & ICT",
])

def summary(series, label):
    top, bot = series.idxmax(), series.idxmin()
    return f"**{top}** at {series.max():.0%} {label}, **{bot}** at {series.min():.0%} (avg {series.mean():.0%})."

# ─── Tab 1: Infrastructure & Facilities ──────────────────────────────────────
with tabs[0]:
    st.header("WASH+ Infrastructure")

    metrics = {
        "Functional Electricity":  "func_electricity",
        "Functional Water":        "func_water",
        "Girls’ Toilets (%)":      "pct_toilet_func_girls",
        "Functional Handwash":     "func_handwash",
    }

    #Pie charts
    cols = st.columns(len(metrics), gap="small")

    for (label, colname), col in zip(metrics.items(), cols):
        val = df_filt[colname].mean()   # compute mean here
        frac = float(val)
        pct_text = f"{frac*100:.0f}%" 
        fig = px.pie(
            names=["Available","Not available"],
            values=[frac, 1 - frac],
            hole=0.6,
            )
        # Style it to look like a KPI
        fig.update_traces(
            marker_colors=[PRIMARY, "#e0e0e0"],
            textinfo="none"
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            width=100, height=100,  # adjust as you like
            annotations=[          # <-- put the percent in the center
                dict(
                    text=pct_text,
                    x=0.5, y=0.5, 
                    font_size=20,
                    font_color=PRIMARY,
                    showarrow=False
                )
            ]
        )

        # Render with the column header as label
        col.markdown(
            f"<div style='text-align: center; font-weight: 600;'>{label}</div>",
            unsafe_allow_html=True
        )
        col.plotly_chart(fig, use_container_width=True,)

    # ————— Metric selector —————
    metrics = {
        "Functional Electricity":  "func_electricity",
        "Functional Water":        "func_water",
        "Girls’ Toilets (%)":      "pct_toilet_func_girls",
        "Functional Handwash":     "func_handwash",
        "Composite Infra Index":   "infra_index",
    }
    
    choice = st.selectbox("Choose a metric to map", list(metrics.keys()))
    col = metrics[choice]
    
    # ─── Two‐column layout ───
    left, right = st.columns([2.5, 2], gap="large")

    # Choropleth
    with open("india_states.geojson") as f:
        gj = json.load(f)

    # ————— Aggregate by state —————
    state_metric = (
        df_filt
        .groupby("state")[col]
        .mean()
        .reset_index()
    )
    state_metric["state"] = state_metric["state"].str.title()

    # ————— Build the choropleth —————
    with left:
        st.subheader(f"Composite Map for {choice}")
        fig = px.choropleth(
            state_metric,
            geojson=gj,
            locations="state",
            featureidkey="properties.ST_NM",
            color=col,
            range_color=(0,1),
            color_continuous_scale=[PRIMARY, SECONDARY],
            labels={col: ""},
            scope="asia",
            projection="mercator",
        )

        # hide geo frame & zoom handles
        #fig.update_geos(fitbounds="locations", visible=False)
        fig.update_geos(
            visible=False,
            center=dict(lat=22.0, lon=80.0),    # approximate center of India
            projection_scale=2.5,               # try 5–8 until it fills nicely
        )
        fig.update_traces(showscale=True)

        # only set margins & title—no width/height
        fig.update_layout(
            #autosize = True,
            margin=dict(l=0, r=0, t=30, b=0),
            #title=dict(text=choice, x=0.5),
        )

        # let Streamlit stretch the map to fill the column
        st.plotly_chart(
            fig,
            use_container_width=False,
            config={"displayModeBar":False, "scrollZoom":False},
            key="choropleth_map",
        )

    # 1) Compute state‐level means for the chosen metric
        ranked = (
            df_filt
            .groupby("state")[col]
            .mean()
            .sort_values(ascending=False)
        )

    # 2) Grab top 10 and bottom 10
    tb = pd.concat([ranked.head(10), ranked.tail(10)]).reset_index()
    tb.columns = ["state", col]      # ensure nice names

    # 3) Build the horizontal bar
    with right:
        st.subheader(f"State Ranking by {choice}")
        fig2 = px.bar(
            tb,
            x=col,
            y="state",
            orientation="h",
            labels={col: choice, "state": "State"},
        )

        # 4) Style it
        fig2.update_traces(marker_color=PRIMARY)
        fig2.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
    )
        st.plotly_chart(
            fig2,
            use_container_width=False,
            width=600,    # slightly wider than the map
            height=400,
            config={"displayModeBar": False},
            key="ranking",
        )
    
    col_mgmt, col_loc = st.columns(2)

    with col_mgmt:
        st.subheader(f"{choice} by Management")
        # aggregate
        mgmt_summary = (
            df_filt
            .groupby("management")[col]  # `col` is your internal column name for the metric
            .mean()
            .reset_index()
            .sort_values(col, ascending=False)
        )
        # bar chart
        fig_mgmt = px.bar(
            mgmt_summary,
            x="management",
            y=col,
            labels={ "management": "Management", col: choice },
            color="management",
            color_discrete_sequence=[PRIMARY, SECONDARY, ACCENT]
        )

        fig_mgmt.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
            height=350,
            xaxis_tickangle=0,
        )
        st.plotly_chart(fig_mgmt, use_container_width=True, config={"displayModeBar": False}, key = "wash_mgmt")


    with col_loc:
        st.subheader(f"{choice} by Location")
        # aggregate
        loc_summary = (
            df_filt
            .groupby("location")[col]    # assumes your df_filt has "location" = "Rural"/"Urban"
            .mean()
            .reset_index()
            .sort_values(col, ascending=False)
        )
        # bar chart
        fig_loc = px.bar(
            loc_summary,
            x="location",
            y=col,
            labels={ "location": "Location", col: choice },
            color="location",
            color_discrete_map={"Urban": PRIMARY, "Rural": SECONDARY},
        )
        fig_loc.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig_loc, use_container_width=True, config={"displayModeBar": False}, key = "wash_loc")
    
# ─── Tab 2: Equity & CWSN ──────────────────────────────────────
with tabs[1]:
    st.header("Equity & Accessibility")

    metrics = {
        "Ramps":  "ramps",
        "Handrails":        "handrails",
        "Girls’ Toilets (%)":      "pct_toilet_func_girls",
    }

    #Pie charts
    cols = st.columns(len(metrics), gap="small")

    for (label, colname), col in zip(metrics.items(), cols):
        val = df_filt[colname].mean()   # compute mean here
        frac = float(val)
        pct_text = f"{frac*100:.0f}%" 
        fig_e = px.pie(
            names=["Available","Not available"],
            values=[frac, 1 - frac],
            hole=0.6,
            )
        # Style it to look like a KPI
        fig_e.update_traces(
            marker_colors=[PRIMARY, "#e0e0e0"],
            textinfo="none"
        )
        fig_e.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            width=100, height=100,  # adjust as you like
            annotations=[          # <-- put the percent in the center
                dict(
                    text=pct_text,
                    x=0.5, y=0.5, 
                    font_size=20,
                    font_color=PRIMARY,
                    showarrow=False
                )
            ]
        )

        # Render with the column header as label
        col.markdown(
            f"<div style='text-align: center; font-weight: 600;'>{label}</div>",
            unsafe_allow_html=True
        )
        eq_donut_key = "eq_donut_" + label.lower().replace(" ", "_").replace("’","")

        col.plotly_chart(fig_e, use_container_width=True, key=eq_donut_key)

    # ————— Metric selector —————
    
    metrics = {
        "Ramps":  "ramps",
        "Handrails":        "handrails",
        "Girls’ Toilets (%)":      "pct_toilet_func_girls",
        "Composite Equity Index": "equity_index",
    }

    choice = st.selectbox("Choose a metric to map", list(metrics.keys()))
    col = metrics[choice]
    
    # ─── Two‐column layout ───
    left, right = st.columns([2.5, 2], gap="large")

    # Choropleth
    with open("india_states.geojson") as f:
        gj = json.load(f)

    # ————— Aggregate by state —————
    state_metric = (
        df_filt
        .groupby("state")[col]
        .mean()
        .reset_index()
    )
    state_metric["state"] = state_metric["state"].str.title()

    # ————— Build the choropleth —————
    with left:
        st.subheader(f"Composite Map for {choice}")
        fig_e2 = px.choropleth(
            state_metric,
            geojson=gj,
            locations="state",
            featureidkey="properties.ST_NM",
            color=col,
            range_color=(0,1),
            color_continuous_scale=[PRIMARY, SECONDARY],
            labels={col: ""},
            scope="asia",
            projection="mercator",
        )

        # hide geo frame & zoom handles
        #fig.update_geos(fitbounds="locations", visible=False)
        fig_e2.update_geos(
            visible=False,
            center=dict(lat=22.0, lon=80.0),    # approximate center of India
            projection_scale=2.5,               # try 5–8 until it fills nicely
        )
        fig_e2.update_traces(showscale=True)

        # only set margins & title—no width/height
        fig_e2.update_layout(
            #autosize = True,
            margin=dict(l=0, r=0, t=30, b=0),
            #title=dict(text=choice, x=0.5),
        )

        # let Streamlit stretch the map to fill the column
        st.plotly_chart(
            fig_e2,
            use_container_width=False,
            config={"displayModeBar":False, "scrollZoom":False},
            key="choropleth_map_eq",
        )

    # 1) Compute state‐level means for the chosen metric
        ranked = (
            df_filt
            .groupby("state")[col]
            .mean()
            .sort_values(ascending=False)
        )

    # 2) Grab top 10 and bottom 10
    tb = pd.concat([ranked.head(10), ranked.tail(10)]).reset_index()
    tb.columns = ["state", col]      # ensure nice names

    # 3) Build the horizontal bar
    with right:
        st.subheader(f"State Ranking by {choice}")
        fig_e3 = px.bar(
            tb,
            x=col,
            y="state",
            orientation="h",
            labels={col: choice, "state": "State"},
        )

        # 4) Style it
        fig_e3.update_traces(marker_color=PRIMARY)
        fig_e3.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
    )
        st.plotly_chart(
            fig_e3,
            use_container_width=False,
            width=600,    # slightly wider than the map
            height=400,
            config={"displayModeBar": False},
            key="ranking_eq",
        )
    
    col_mgmt, col_loc = st.columns(2)

    with col_mgmt:
        st.subheader(f"{choice} by Management")
        # aggregate
        mgmt_summary = (
            df_filt
            .groupby("management")[col]  # `col` is your internal column name for the metric
            .mean()
            .reset_index()
            .sort_values(col, ascending=False)
        )
        # bar chart
        fig_e_mgmt = px.bar(
            mgmt_summary,
            x="management",
            y=col,
            labels={ "management": "Management", col: choice },
            color="management",
            color_discrete_sequence=[PRIMARY, SECONDARY, ACCENT]
        )

        fig_e_mgmt.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
            height=350,
            xaxis_tickangle=0,
        )
        st.plotly_chart(fig_e_mgmt, use_container_width=True, config={"displayModeBar": False}, key = "eq_mgmt")


    with col_loc:
        st.subheader(f"{choice} by Location")
        # aggregate
        loc_summary = (
            df_filt
            .groupby("location")[col]    # assumes your df_filt has "location" = "Rural"/"Urban"
            .mean()
            .reset_index()
            .sort_values(col, ascending=False)
        )
        # bar chart
        fig_e_loc = px.bar(
            loc_summary,
            x="location",
            y=col,
            labels={ "location": "Location", col: choice },
            color="location",
            color_discrete_map={"Urban": PRIMARY, "Rural": SECONDARY},
        )
        fig_e_loc.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig_e_loc, use_container_width=True, config={"displayModeBar": False}, key = "eq_loc")
    
    dig_s = pd.Series({
        "Internet":  df_filt["internet"].mean(),
        "ICT Labs":  df_filt["ict_lab"].mean(),
        "Computers": df_filt["desktop"].mean(),
    })

    d1, d2, d3 = st.columns(3)
    d1.metric("Internet (avail %)", f"{dig_s['Internet']:.0%}")
    d2.metric("ICT Labs (avail %)", f"{dig_s['ICT Labs']:.0%}")
    d3.metric("Avg PCs/School", f"{dig_s['Computers']:.1f}")

# ─── Tab 3: Digital & ICT ───────────────────────────────────────────────────
with tabs[2]:
    st.header("Digital & ICT Readiness")

    metrics = {
        "Internet":  "internet",
        "ICT Labs":   "ict_lab",
        "Computers":  "computer_yn",
    }

    #Pie charts
    cols = st.columns(len(metrics), gap="small")

    for (label, colname), col in zip(metrics.items(), cols):
        val = df_filt[colname].mean()   # compute mean here
        frac = float(val)
        pct_text = f"{frac*100:.0f}%" 
        fig_e = px.pie(
            names=["Available","Not available"],
            values=[frac, 1 - frac],
            hole=0.6,
            )
        # Style it to look like a KPI
        fig_e.update_traces(
            marker_colors=[PRIMARY, "#e0e0e0"],
            textinfo="none"
        )
        fig_e.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            width=100, height=100,  # adjust as you like
            annotations=[          # <-- put the percent in the center
                dict(
                    text=pct_text,
                    x=0.5, y=0.5, 
                    font_size=20,
                    font_color=PRIMARY,
                    showarrow=False
                )
            ]
        )

        # Render with the column header as label
        col.markdown(
            f"<div style='text-align: center; font-weight: 600;'>{label}</div>",
            unsafe_allow_html=True
        )
        dig_donut_key = "dig_donut_" + label.lower().replace(" ", "_").replace("’","")

        col.plotly_chart(fig_e, use_container_width=True, key=dig_donut_key)

    dig_s = pd.Series({
        "Internet":  df_filt["internet"].mean(),
        "ICT Labs":  df_filt["ict_lab"].mean(),
        "Computers": df_filt["desktop"].mean(),
    })

    d1, d2, d3 = st.columns(3)
    d1.metric("Internet (avail %)", f"{dig_s['Internet']:.0%}")
    d2.metric("ICT Labs (avail %)", f"{dig_s['ICT Labs']:.0%}")
    d3.metric("Avg PCs/School", f"{dig_s['Computers']:.1f}")


    # ————— Metric selector —————
    
    metrics = {
        "Internet":  "internet",
        "ICT Labs":   "ict_lan",
        "Computers":  "computer_yn",
    }

    choice = st.selectbox("Choose a metric to map", list(metrics.keys()))
    col = metrics[choice]
    
    # ─── Two‐column layout ───
    left, right = st.columns([2.5, 2], gap="large")

    # Choropleth
    with open("india_states.geojson") as f:
        gj = json.load(f)

    # ————— Aggregate by state —————
    state_metric = (
        df_filt
        .groupby("state")[col]
        .mean()
        .reset_index()
    )
    state_metric["state"] = state_metric["state"].str.title()

    # ————— Build the choropleth —————
    with left:
        st.subheader(f"Composite Map for {choice}")
        fig_e2 = px.choropleth(
            state_metric,
            geojson=gj,
            locations="state",
            featureidkey="properties.ST_NM",
            color=col,
            range_color=(0,1),
            color_continuous_scale=[PRIMARY, SECONDARY],
            labels={col: ""},
            scope="asia",
            projection="mercator",
        )

        # hide geo frame & zoom handles
        #fig.update_geos(fitbounds="locations", visible=False)
        fig_e2.update_geos(
            visible=False,
            center=dict(lat=22.0, lon=80.0),    # approximate center of India
            projection_scale=2.5,               # try 5–8 until it fills nicely
        )
        fig_e2.update_traces(showscale=True)

        # only set margins & title—no width/height
        fig_e2.update_layout(
            #autosize = True,
            margin=dict(l=0, r=0, t=30, b=0),
            #title=dict(text=choice, x=0.5),
        )

        # let Streamlit stretch the map to fill the column
        st.plotly_chart(
            fig_e2,
            use_container_width=False,
            config={"displayModeBar":False, "scrollZoom":False},
            key="choropleth_map_dig",
        )

    # 1) Compute state‐level means for the chosen metric
        ranked = (
            df_filt
            .groupby("state")[col]
            .mean()
            .sort_values(ascending=False)
        )

    # 2) Grab top 10 and bottom 10
    tb = pd.concat([ranked.head(10), ranked.tail(10)]).reset_index()
    tb.columns = ["state", col]      # ensure nice names

    # 3) Build the horizontal bar
    with right:
        st.subheader(f"State Ranking by {choice}")
        fig_e3 = px.bar(
            tb,
            x=col,
            y="state",
            orientation="h",
            labels={col: choice, "state": "State"},
        )

        # 4) Style it
        fig_e3.update_traces(marker_color=PRIMARY)
        fig_e3.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
    )
        st.plotly_chart(
            fig_e3,
            use_container_width=False,
            width=600,    # slightly wider than the map
            height=400,
            config={"displayModeBar": False},
            key="ranking_dig",
        )
    
    col_mgmt, col_loc = st.columns(2)

    with col_mgmt:
        st.subheader(f"{choice} by Management")
        # aggregate
        mgmt_summary = (
            df_filt
            .groupby("management")[col]  # `col` is your internal column name for the metric
            .mean()
            .reset_index()
            .sort_values(col, ascending=False)
        )
        # bar chart
        fig_e_mgmt = px.bar(
            mgmt_summary,
            x="management",
            y=col,
            labels={ "management": "Management", col: choice },
            color="management",
            color_discrete_sequence=[PRIMARY, SECONDARY, ACCENT]
        )

        fig_e_mgmt.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
            height=350,
            xaxis_tickangle=0,
        )
        st.plotly_chart(fig_e_mgmt, use_container_width=True, config={"displayModeBar": False}, key = "dig_mgmt")


    with col_loc:
        st.subheader(f"{choice} by Location")
        # aggregate
        loc_summary = (
            df_filt
            .groupby("location")[col]    # assumes your df_filt has "location" = "Rural"/"Urban"
            .mean()
            .reset_index()
            .sort_values(col, ascending=False)
        )
        # bar chart
        fig_e_loc = px.bar(
            loc_summary,
            x="location",
            y=col,
            labels={ "location": "Location", col: choice },
            color="location",
            color_discrete_map={"Urban": PRIMARY, "Rural": SECONDARY},
        )
        fig_e_loc.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig_e_loc, use_container_width=True, config={"displayModeBar": False}, key = "dig_loc")
    

