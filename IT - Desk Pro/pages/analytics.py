"""
IT DeskPro - Analytics & Reports Console
Executive reporting, SLA resolution rates, Plotly visualizations, and CSV data export.
"""
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from utils.authentication import check_role_access
from utils.analytics import (
    get_analytics_dataframe,
    calculate_kpis,
    plot_tickets_by_category,
    plot_tickets_by_status,
    plot_tickets_by_priority,
    plot_monthly_trend
)
from utils.ui_components import render_welcome_banner, render_kpi_card


def render_analytics_page():
    """Renders executive ticket analytics and export reports."""
    if not check_role_access(["IT Support", "Admin"]):
        return

    render_welcome_banner(
        title="Ticket Analytics & Performance Reports",
        subtitle="Analyze ticket volumes, incident categories, priority distributions, and resolution SLAs."
    )

    # Date Range Filters
    st.markdown('<div class="content-box">', unsafe_allow_html=True)
    st.markdown('<div class="content-box-header">Filter by Date Range</div>', unsafe_allow_html=True)

    col_d1, col_d2, col_preset = st.columns([2, 2, 3])

    # Date range default: past 6 months to today
    today = datetime.now().date()
    default_start = today - timedelta(days=180)

    with col_preset:
        preset = st.selectbox(
            "Quick Date Preset",
            ["Past 6 Months", "Past 30 Days", "Past 90 Days", "Year to Date", "All Time"]
        )
        if preset == "Past 30 Days":
            default_start = today - timedelta(days=30)
        elif preset == "Past 90 Days":
            default_start = today - timedelta(days=90)
        elif preset == "Year to Date":
            default_start = datetime(today.year, 1, 1).date()
        elif preset == "All Time":
            default_start = datetime(2020, 1, 1).date()

    with col_d1:
        start_date = st.date_input("Start Date", value=default_start)
    with col_d2:
        end_date = st.date_input("End Date", value=today)

    st.markdown('</div>', unsafe_allow_html=True)

    # Query Data using Pandas
    df = get_analytics_dataframe(start_date=start_date, end_date=end_date)
    kpis = calculate_kpis(df)

    # KPI Summary Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Tickets in Period", kpis["total_tickets"], f"From {start_date} to {end_date}", "#2563EB")
    with k2:
        render_kpi_card("Resolution Rate", kpis["resolution_rate"], f"{kpis['resolved_count']} resolved/closed", "#10B981")
    with k3:
        render_kpi_card("Avg Resolution SLA", kpis["avg_resolution_time"], "From creation to resolution", "#6366F1")
    with k4:
        render_kpi_card("Critical Incidents", kpis["critical_tickets"], "Severity 1 issues", "#EF4444")

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    if df.empty:
        st.info("No tickets were found for the selected date range. Try broadening your filter.")
        return

    # Visualizations Grid
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        st.plotly_chart(plot_tickets_by_category(df), use_container_width=True)
    with row1_c2:
        st.plotly_chart(plot_tickets_by_status(df), use_container_width=True)

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        st.plotly_chart(plot_tickets_by_priority(df), use_container_width=True)
    with row2_c2:
        st.plotly_chart(plot_monthly_trend(df), use_container_width=True)

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    # Export & Data Table Section
    st.markdown('<div class="content-box">', unsafe_allow_html=True)
    st.markdown('<div class="content-box-header">Ticket Records & Data Export</div>', unsafe_allow_html=True)

    # Export to CSV
    export_df = df[[
        "ticket_number", "employee_name", "employee_email", "title",
        "category", "priority", "status", "created_at", "updated_at",
        "resolved_at", "resolution_hours"
    ]].copy()

    csv_data = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Export Filtered Tickets to CSV",
        data=csv_data,
        file_name=f"IT_DeskPro_Tickets_{start_date}_to_{end_date}.csv",
        mime="text/csv",
        type="primary"
    )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.dataframe(export_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

