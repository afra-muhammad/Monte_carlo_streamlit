import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import math
from monte_carlo import run_monte_carlo, Flow_rate, Heat_Energy

st.title("Monte Carlo Simulation of Shower CO2 Emissions")

st.warning("🔧 Please enable *Wide mode* in Settings (top-right menu) for best display!")

MAX_BINS = 30

# User inputs
N = st.number_input(
    "Number of simulations (min=100, max=20000)",
    min_value=100,
    max_value=20000,
    value=1000,
    step=100
)

seed = st.number_input(
    "Random seed (min=0, max=9999)",
    min_value=0,
    max_value=9999,
    value=1350,
    step=1
)

# Shower time distribution input method
mode = st.selectbox(
    "Shower time distribution input method",
    ("Mean & Standard Deviation", "Direct μ & σ")
)

if mode == "Mean & Standard Deviation":
    mean = st.number_input(
        "Mean shower time in minutes (min=1, max=60)",
        min_value=1.0,
        max_value=60.0,
        value=10.0,
        step=0.5
    )
    std = st.number_input(
        "Standard deviation in minutes (min=0.1, max=30)",
        min_value=0.1,
        max_value=30.0,
        value=3.0,
        step=0.1
    )
    variance = std ** 2
    mu = math.log((mean ** 2) / math.sqrt(variance + mean ** 2))
    sigma = math.sqrt(math.log(1 + (variance / mean ** 2)))
else:
    mu = st.number_input("Lognormal μ (min=0, max=15)", min_value=0.0, max_value=5.0, value=2.2, step=0.01)
    sigma = st.number_input("Lognormal σ (min=0.01, max=5)", min_value=0.01, max_value=2.0, value=0.28, step=0.01)

# Placeholders
progress_bar = st.empty()
status_text = st.empty()

# Run simulation
st.write(f"Running Monte Carlo simulation with {N} iterations...")

def progress_callback(progress):
    progress_bar.progress(int(progress * 100))
    status_text.text(f"{int(progress * 100)}% complete")

df_sim = run_monte_carlo(
    N=N,
    mu=mu,
    sigma=sigma,
    Flow_rate=Flow_rate,
    Heat_Energy=Heat_Energy,
    seed=seed,
    progress_callback=progress_callback
)

progress_bar.empty()
status_text.text("Simulation done!")

# Histogram plotting function
def plot_histogram_with_stats(df, column, title, color):
    st.subheader(title)
    max_val = df[column].max() * 1.05

    col_stats, col_pct, col_count = st.columns([2, 7, 7])

    with col_stats:
        st.write("Summary statistics")
        st.write(df[column].describe(percentiles=[0.05, 0.5, 0.95]))

    # Percentage histogram
    with col_pct:
        hist_pct = (
            alt.Chart(df)
            .transform_bin("binned", column, bin=alt.Bin(maxbins=MAX_BINS))
            .transform_aggregate(count='count()', groupby=['binned'])
            .transform_calculate(pct=f'datum.count / {len(df)}')
            .mark_bar(color=color)
            .encode(
                alt.X('binned:Q', title=title, scale=alt.Scale(domain=[0, max_val])),
                alt.Y('pct:Q', axis=alt.Axis(format='%'), title='Percentage')
            )
            .properties(height=300, title=f"{title} (%)")
        )
        st.altair_chart(hist_pct, use_container_width=True)

    # Count histogram
    with col_count:
        hist_count = (
            alt.Chart(df)
            .transform_bin("binned", column, bin=alt.Bin(maxbins=MAX_BINS))
            .transform_aggregate(count='count()', groupby=['binned'])
            .mark_bar(color=color, opacity=0.6)
            .encode(
                alt.X('binned:Q', title=title, scale=alt.Scale(domain=[0, max_val])),
                alt.Y('count:Q', title='Count')
            )
            .properties(height=300, title=f"{title} (Count)")
        )
        st.altair_chart(hist_count, use_container_width=True)

# Total CO2
plot_histogram_with_stats(df_sim, 'CO2_Total', 'Total CO2 Emissions (kg)', '#1f77b4')

# Total CO2 : boxplot

st.subheader("Boxplot: Total CO₂ Emissions")

st.subheader("Boxplot: Total CO₂ Emissions")

box = (
    alt.Chart(df_sim)
    .mark_boxplot(size=40)
    .encode(
        x=alt.X('CO2_Total:Q', title="Total CO₂ Emissions (kg)"),
        tooltip=[
            alt.Tooltip('CO2_Total:Q', title="Total CO₂ (kg)", format=".3f")
        ]
    )
    .properties(height=100)
)

st.altair_chart(box, use_container_width=True)

# Water CO2 filter
st.subheader("Filter CO2 from Water by Source")
water_sources = df_sim['Water_Source'].unique().tolist()

if 'water_selection' not in st.session_state:
    st.session_state.water_selection = water_sources.copy()

def select_all_water():
    st.session_state.water_selection = water_sources.copy()
def deselect_all_water():
    st.session_state.water_selection = []

col1, col2 = st.columns(2)
with col1:
    st.button("Select All Water Sources", on_click=select_all_water)
with col2:
    st.button("Deselect All Water Sources", on_click=deselect_all_water)

selected_water_sources = st.multiselect(
    "Select Water Source(s)",
    options=water_sources,
    key="water_selection"
)

df_water_filtered = df_sim[df_sim['Water_Source'].isin(st.session_state.water_selection)]
if df_water_filtered.empty:
    st.warning("No Water Source selected! Please select at least one source.")
else:
    plot_histogram_with_stats(df_water_filtered, 'CO2_Water', 'CO2 from Water (kg)', '#ff7f0e')

# Heat CO2 filter
st.subheader("Filter CO2 from Heat by Source")
heat_sources = df_sim['Heat_Source'].unique().tolist()

if 'heat_selection' not in st.session_state:
    st.session_state.heat_selection = heat_sources.copy()

def select_all_heat():
    st.session_state.heat_selection = heat_sources.copy()
def deselect_all_heat():
    st.session_state.heat_selection = []

col1, col2 = st.columns(2)
with col1:
    st.button("Select All Heat Sources", on_click=select_all_heat)
with col2:
    st.button("Deselect All Heat Sources", on_click=deselect_all_heat)

selected_heat_sources = st.multiselect(
    "Select Heat Source(s)",
    options=heat_sources,
    key="heat_selection"
)

df_heat_filtered = df_sim[df_sim['Heat_Source'].isin(st.session_state.heat_selection)]
if df_heat_filtered.empty:
    st.warning("No Heat Source selected! Please select at least one source.")
else:
    plot_histogram_with_stats(df_heat_filtered, 'CO2_Heat', 'CO2 from Heat (kg)', '#2ca02c')

# Shower Duration
plot_histogram_with_stats(df_sim, 'Shower_time_min', 'Shower Duration (minutes)', '#d62728')

# Simulation table
st.subheader("Full Simulation Data (up to 1000 rows)")
st.dataframe(df_sim.head(1000))