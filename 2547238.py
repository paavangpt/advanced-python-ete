import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import re

st.set_page_config(page_title="GATEWAYS 2025", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("dataset.csv")

df = load_data()

# Sidebar filters
st.sidebar.title("Filters")
sel_state   = st.sidebar.selectbox("State",   ["All"] + sorted(df["State"].unique()))
sel_event   = st.sidebar.selectbox("Event",   ["All"] + sorted(df["Event Name"].unique()))
sel_college = st.sidebar.selectbox("College", ["All"] + sorted(df["College"].unique()))
sel_rating  = st.sidebar.slider("Min Rating", 1, 5, 1)

dff = df.copy()
if sel_state   != "All": dff = dff[dff["State"]      == sel_state]
if sel_event   != "All": dff = dff[dff["Event Name"] == sel_event]
if sel_college != "All": dff = dff[dff["College"]    == sel_college]
dff = dff[dff["Rating"] >= sel_rating]

SCHEME = "Blues"

# Simplified bar helper — color axis is hidden anyway, so no need to switch on orientation
def bar(data, x, y, **kw):
    fig = px.bar(data, x=x, y=y, text=y, color_continuous_scale=SCHEME, **kw)
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False, height=320)
    return fig

# Helper: value_counts → clean two-column DataFrame in one line
def vc(series, col):
    df_ = series.value_counts().reset_index()
    df_.columns = [col, "Count"]
    return df_

# Header
st.title("GATEWAYS 2025 - Participation Dashboard")
st.caption("National Level Fest · Analytics Dashboard")
st.divider()

# KPIs
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Participants", len(dff))
k2.metric("Colleges",     dff["College"].nunique())
k3.metric("States",       dff["State"].nunique())
k4.metric("Events",       dff["Event Name"].nunique())
k5.metric("Avg Rating",   f"{dff['Rating'].mean():.2f}" if len(dff) else "-")

st.divider()

tab1, tab2, tab3 = st.tabs(["Participation Trends", "Feedback & Ratings", "Data Explorer"])

with tab1:
    st.subheader("State-wise Participants - India Map")
    state_counts = vc(dff["State"], "State").rename(columns={"Count": "Participants"})
    fig_map = px.choropleth(
        state_counts,
        geojson="https://raw.githubusercontent.com/geohacker/india/master/state/india_telengana.geojson",
        locations="State", featureidkey="properties.NAME_1",
        color="Participants", color_continuous_scale=SCHEME, hover_name="State",
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(height=480, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("State-wise Count")
    st.plotly_chart(bar(state_counts.sort_values("Participants", ascending=False),
                        "State", "Participants"), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Event-wise Participation")
        ev = vc(dff["Event Name"], "Event")
        fig = bar(ev, "Count", "Event", orientation="h")
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("College-wise Participation")
        col_cnt = vc(dff["College"], "College")
        fig = bar(col_cnt, "Count", "College", orientation="h")
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Individual vs Group")
        et = vc(dff["Event Type"], "Type")
        st.plotly_chart(px.pie(et, names="Type", values="Count", hole=0.4,
                               color_discrete_sequence=px.colors.sequential.Blues_r),
                        use_container_width=True)
    with c4:
        st.subheader("Revenue by Event")
        rev = dff.groupby("Event Name")["Amount Paid"].sum().reset_index()
        rev.columns = ["Event", "Revenue"]
        fig = bar(rev.sort_values("Revenue", ascending=False), "Event", "Revenue")
        fig.update_traces(texttemplate="Rs.%{text}")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Rating Distribution")
        rat = dff["Rating"].value_counts().sort_index().reset_index()
        rat.columns = ["Rating", "Count"]
        rat["Label"] = rat["Rating"].astype(str) + " stars"
        st.plotly_chart(bar(rat, "Label", "Count"), use_container_width=True)
    with c2:
        st.subheader("Avg Rating by Event")
        avg_rat = dff.groupby("Event Name")["Rating"].mean().reset_index()
        avg_rat.columns = ["Event", "Avg Rating"]
        fig = bar(avg_rat.sort_values("Avg Rating"), "Avg Rating", "Event", orientation="h")
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Feedback Keywords")
    STOPWORDS = {"and","the","is","in","of","to","a","an","it","for","on",
                 "with","at","by","this","was","are","be","but","as","or","very"}
    words = re.findall(r'\b[a-z]{3,}\b', " ".join(dff["Feedback on Fest"].dropna().str.lower()))
    freq = Counter(w for w in words if w not in STOPWORDS)
    top_words = pd.DataFrame(freq.most_common(15), columns=["Word", "Count"])
    fig = bar(top_words, "Count", "Word", orientation="h")
    fig.update_layout(height=420, yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sentiment Summary")
    sentiment = dff["Rating"].apply(
        lambda r: "Positive" if r >= 4 else ("Neutral" if r == 3 else "Negative")
    )
    sent = vc(sentiment, "Sentiment")
    st.plotly_chart(px.pie(sent, names="Sentiment", values="Count", hole=0.4,
                           color="Sentiment",
                           color_discrete_map={"Positive": "#1a6faf",
                                               "Neutral":  "#74b3d8",
                                               "Negative": "#cce4f4"}),
                    use_container_width=True)

with tab3:
    st.subheader("Raw Data Explorer")
    search_q = st.text_input("Search", placeholder="e.g. Anna University")
    display_df = dff.copy()
    if search_q:
        mask = display_df.apply(
            lambda col: col.astype(str).str.contains(search_q, case=False, na=False)
        ).any(axis=1)
        display_df = display_df[mask]
    st.dataframe(display_df, use_container_width=True, height=460)
    st.caption(f"Showing {len(display_df)} of {len(dff)} filtered rows")
    st.download_button("Download as CSV", display_df.to_csv(index=False),
                       "gateways2025_filtered.csv", "text/csv")