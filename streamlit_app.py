import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------
# Load Data
# ----------------------
@st.cache_data
def load_data():
    url = 'https://raw.githubusercontent.com/dnlaql/cls-reporting/refs/heads/main/Data/workorder_with_sla%20(1).csv'
    df = pd.read_csv(url)

    # Convert date columns
    df["Date Created"] = pd.to_datetime(df["Date Created"], errors='coerce')
    df["To Do Dt"] = pd.to_datetime(df["To Do Dt"], errors='coerce')

    # Map boolean to PASS/FAIL
    df["SLA_Respond_Status"] = df["SLA_Respond_Met"].map({True: "PASS", False: "FAIL"})
    df["SLA_Resolution_Status"] = df["SLA_Resolution_Met"].map({True: "PASS", False: "FAIL"})

    return df

df = load_data()

# ----------------------
# Sidebar Filters
# ----------------------
st.sidebar.title("Filters")

priorities = st.sidebar.multiselect("Select Priority", options=df["Priority"].unique(), default=df["Priority"].unique())
assignees = st.sidebar.multiselect("Select Assignee", options=df["Assign To"].unique(), default=df["Assign To"].unique())
date_range = st.sidebar.date_input("Select Date Range", [df["Date Created"].min(), df["Date Created"].max()])

# Add Sub Category Filter if available
if "Sub Category" in df.columns:
    subcategories = st.sidebar.multiselect("Select Sub Category", options=df["Sub Category"].dropna().unique(), default=df["Sub Category"].dropna().unique())
else:
    subcategories = []

# Filter data
filtered_df = df[
    (df["Priority"].isin(priorities)) &
    (df["Assign To"].isin(assignees)) &
    (df["Date Created"].dt.date >= date_range[0]) &
    (df["Date Created"].dt.date <= date_range[1])
]

if "Sub Category" in df.columns:
    filtered_df = filtered_df[filtered_df["Sub Category"].isin(subcategories)]

# ----------------------
# KPI Cards (Vertical Style)
# ----------------------
st.title("Work Order SLA Dashboard")

left_col, right_col = st.columns(2)

with left_col:
    st.metric("Total Work Orders", len(filtered_df))
    st.metric("Avg Response Time (min)", round(filtered_df["Response Time (min)"].mean(), 2))

with right_col:
    st.metric("SLA Response PASS %", f"{(filtered_df['SLA_Respond_Met'] == True).mean() * 100:.1f}%")
    st.metric("SLA Resolution PASS %", f"{(filtered_df['SLA_Resolution_Met'] == True).mean() * 100:.1f}%")

# ----------------------
# Charts
# ----------------------
st.subheader("SLA Compliance by Priority")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    respond_fig = px.histogram(
        filtered_df,
        x="Priority",
        color="SLA_Respond_Status",
        barmode="group",
        title="Response SLA Compliance by Priority"
    )
    st.plotly_chart(respond_fig, use_container_width=True)

with chart_col2:
    resolution_fig = px.histogram(
        filtered_df,
        x="Priority",
        color="SLA_Resolution_Status",
        barmode="group",
        title="Resolution SLA Compliance by Priority"
    )
    st.plotly_chart(resolution_fig, use_container_width=True)

# ----------------------
# Average Times by Priority
# ----------------------
st.subheader("Average Times by Priority")
time_df = filtered_df.groupby("Priority")[["Response Time (min)", "Resolution Time (min)"]].mean().reset_index()
time_fig = px.bar(
    time_df.melt(id_vars="Priority", var_name="Metric", value_name="Minutes"),
    x="Priority", y="Minutes", color="Metric", barmode="group",
    title="Average Response & Resolution Time by Priority"
)
st.plotly_chart(time_fig, use_container_width=True)

# ----------------------
# SLA Breach by Assignee
# ----------------------
st.subheader("SLA Breaches by Assignee")
breach_df = filtered_df[(filtered_df["SLA_Respond_Met"] == False) | (filtered_df["SLA_Resolution_Met"] == False)]
breach_count = breach_df["Assign To"].value_counts().reset_index()
breach_count.columns = ["Assign To", "SLA Breaches"]

breach_fig = px.bar(breach_count, x="Assign To", y="SLA Breaches", title="SLA Breach Count by Assignee")
st.plotly_chart(breach_fig, use_container_width=True)

# ----------------------
# SLA Status Pie Charts
# ----------------------
st.subheader("SLA Status Distribution")
pie_col1, pie_col2 = st.columns(2)

with pie_col1:
    response_pie = filtered_df["SLA_Respond_Status"].value_counts().reset_index()
    response_pie.columns = ["Status", "Count"]
    response_pie_fig = px.pie(response_pie, names="Status", values="Count", title="SLA Response PASS vs FAIL")
    st.plotly_chart(response_pie_fig, use_container_width=True)

with pie_col2:
    resolution_pie = filtered_df["SLA_Resolution_Status"].value_counts().reset_index()
    resolution_pie.columns = ["Status", "Count"]
    resolution_pie_fig = px.pie(resolution_pie, names="Status", values="Count", title="SLA Resolution PASS vs FAIL")
    st.plotly_chart(resolution_pie_fig, use_container_width=True)

# ----------------------
# Data Table
# ----------------------
st.subheader("Detailed Work Orders Table")
st.dataframe(filtered_df, use_container_width=True)
