import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.optimize import newton
from io import StringIO

# Load Excel data
@st.cache_data
def load_data(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    cash_flows = pd.read_excel(xls, sheet_name="Sheet1")
    metadata = pd.read_excel(xls, sheet_name="Sheet2")
    try:
        grouping = pd.read_excel(xls, sheet_name="Sheet3")
        grouping_columns = grouping.columns.tolist()
    except:
        grouping_columns = []
    return cash_flows, metadata, grouping_columns

# Calculate XIRR
def xirr(cash_flows):
    if len(cash_flows) < 2:
        return np.nan

    # Ensure at least one positive and one negative cash flow
    values = [cf for _, cf in cash_flows]
    if not any(v > 0 for v in values) or not any(v < 0 for v in values):
        return np.nan

    def xnpv(rate):
        t0 = cash_flows[0][0]
        return sum([cf / (1 + rate) ** ((t - t0).days / 365.0) for t, cf in cash_flows])

    try:
        return round(newton(xnpv, 0.1) * 100, 2)
    except:
        return np.nan

# Streamlit UI
st.title("IRR Calculator by Categories")

uploaded_file = st.file_uploader("Upload IRR Excel File", type=["xlsx"])

if uploaded_file:
    cash_flows, metadata, uploaded_group_columns = load_data(uploaded_file)

    st.sidebar.header("Filter Options")

    # Display dynamic filters from metadata
    selected_filters = {}
    for col in metadata.columns:
        if col == "Deal":
            continue
        options = metadata[col].dropna().unique().tolist()
        selected = st.sidebar.multiselect(f"Select {col}", options, default=options)
        selected_filters[col] = selected

    fund_options = cash_flows["Fund"].dropna().unique().tolist()
    selected_funds = st.sidebar.multiselect("Select Funds (Portfolio)", fund_options, default=fund_options)

    # Date filter
    min_date = cash_flows["Date"].min()
    max_date = cash_flows["Date"].max()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

    # Filter metadata based on dynamic filters
    deal_filter = metadata.copy()
    for key, values in selected_filters.items():
        deal_filter = deal_filter[deal_filter[key].isin(values)]
    filtered_deals = deal_filter["Deal"].tolist()

    filtered_cash_flows = cash_flows[
        (cash_flows["Deal Code"].isin(filtered_deals)) &
        (cash_flows["Fund"].isin(selected_funds)) &
        (cash_flows["Date"] >= pd.to_datetime(date_range[0])) &
        (cash_flows["Date"] <= pd.to_datetime(date_range[1]))
    ]

    # Merge with metadata
    merged_df = filtered_cash_flows.merge(metadata, left_on="Deal Code", right_on="Deal")

    # Group by categories and calculate IRR
        dynamic_columns = [col for col in metadata.columns if col != "Deal"]
    # Add optional 'Year' column from cash flow dates
    merged_df["Year"] = pd.to_datetime(merged_df["Date"]).dt.year

    # Let user select grouping columns
    available_group_fields = dynamic_columns + ["Fund", "Year"]
        default_groups = uploaded_group_columns if uploaded_group_columns else available_group_fields
        if uploaded_group_columns:
        st.sidebar.info(f"Grouping columns loaded from Sheet3: {uploaded_group_columns}")
    else:
        st.sidebar.warning("No Sheet3 found. Default grouping used.")

    group_columns = st.sidebar.multiselect("Group IRR Results By", available_group_fields, default=default_groups), default=dynamic_columns + ["Fund"])
    irr_results = []
skipped_groups = []

    for group_keys, group_df in merged_df.groupby(group_columns):
        cf_series = group_df.groupby("Date")["Amount"].sum().sort_index()
        cash_flow_list = list(zip(cf_series.index, cf_series.values))
                irr = xirr(cash_flow_list)
        if np.isnan(irr):
            skipped_groups.append(dict(zip(group_columns, group_keys)))
        irr_results.append(dict(zip(group_columns, group_keys), IRR=irr))

    result_df = pd.DataFrame(irr_results)
        st.subheader("Calculated IRRs by Category")
    st.dataframe(result_df)

    if skipped_groups:
        st.warning("Some groups were skipped due to missing positive or negative cash flows:")
        st.dataframe(pd.DataFrame(skipped_groups))

    avg_irr = result_df['IRR'].mean()
    st.metric("Average IRR", f"{avg_irr:.2f}%")

    # Deal-level IRR summary
    st.subheader("Deal-Level IRRs")
    deal_irr_list = []
skipped_deals = []
    for deal in merged_df["Deal Code"].unique():
        deal_df = merged_df[merged_df["Deal Code"] == deal]
        cf_series = deal_df.groupby("Date")["Amount"].sum().sort_index()
        cash_flow_list = list(zip(cf_series.index, cf_series.values))
                irr = xirr(cash_flow_list)
        if np.isnan(irr):
            skipped_deals.append(deal)
        deal_irr_list.append({"Deal Code": deal, "IRR (%)": irr})
    deal_result_df = pd.DataFrame(deal_irr_list)
        st.dataframe(deal_result_df)

    if skipped_deals:
        st.warning("The following deals were skipped due to invalid cash flow structure:")
        st.write(skipped_deals)

    # Chart IRRs by category
    st.subheader("IRR Chart by Category")
    chart_df = result_df.dropna(subset=['IRR'])
    if not chart_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        labels = chart_df.apply(lambda row: f"{row['Industry']} | {row['Region']} | {row['Fund']}", axis=1)
        ax.bar(labels, chart_df['IRR'])
        ax.set_ylabel("IRR (%)")
        ax.set_title("IRR by Category")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    # Export results
    st.subheader("Export Results")
    category_csv = StringIO()
    deal_csv = StringIO()
    result_df.to_csv(category_csv, index=False)
    deal_result_df.to_csv(deal_csv, index=False)
    st.download_button("Download Category IRRs as CSV", category_csv.getvalue(), "category_irrs.csv")
    st.download_button("Download Deal IRRs as CSV", deal_csv.getvalue(), "deal_irrs.csv")

    # Export to Excel with multiple sheets
    excel_buffer = StringIO()
    with pd.ExcelWriter("irr_results.xlsx", engine='openpyxl') as writer:
        result_df.to_excel(writer, sheet_name='Category IRRs', index=False)
        deal_result_df.to_excel(writer, sheet_name='Deal IRRs', index=False)
        if skipped_groups:
            pd.DataFrame(skipped_groups).to_excel(writer, sheet_name='Skipped Groups', index=False)
        if skipped_deals:
            pd.DataFrame({"Skipped Deals": skipped_deals}).to_excel(writer, sheet_name='Skipped Deals', index=False)

    with open("irr_results.xlsx", "rb") as f:
        st.download_button("Download All Results as Excel", f.read(), "irr_results.xlsx")
