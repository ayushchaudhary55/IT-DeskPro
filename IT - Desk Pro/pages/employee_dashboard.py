"""
IT DeskPro - Employee Dashboard Page
Displays personal ticket metrics, recent requests, and quick ticket creation CTA.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.authentication import check_role_access, get_current_user
from utils.ticket_functions import get_employee_dashboard_metrics
from utils.ui_components import render_kpi_card, render_welcome_banner, status_badge_html, priority_badge_html
import config


def render_employee_dashboard():
    """Renders the employee's personal dashboard with live MySQL metrics."""
    if not check_role_access(["Employee", "IT Support", "Admin"]):
        return

    current_user = get_current_user()
    user_id = current_user["id"]
    metrics = get_employee_dashboard_metrics(user_id)

    render_welcome_banner(
        title=f"Welcome back, {current_user['full_name']} 👋",
        subtitle="Track your technical support requests, view resolution history, and request IT assistance."
    )

    # Top CTA Bar
    col_cta1, col_cta2 = st.columns([3, 1])
    with col_cta1:
        st.markdown(
            f"<div style='font-size:0.95rem; color:#475569; padding-top:8px;'>"
            f"Employee Account: <b>{current_user['email']}</b>"
            f"</div>",
            unsafe_allow_html=True
        )
    with col_cta2:
        if st.button("➕ Create New Ticket", type="primary", use_container_width=True):
            st.session_state["current_page"] = "Create Ticket"
            st.rerun()

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    # KPI Metrics Row
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        render_kpi_card("Total Submitted", metrics["total"], "All time tickets", "#2563EB")
    with kpi_col2:
        render_kpi_card("Open Tickets", metrics["open"], "Awaiting assignment", "#3B82F6")
    with kpi_col3:
        render_kpi_card("In Progress", metrics["in_progress"], "Under active investigation", "#D97706")
    with kpi_col4:
        render_kpi_card("Resolved", metrics["resolved"] + metrics["closed"], "Completed requests", "#10B981")

    st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)

    # Breakdown & Recent Tickets
    col_chart, col_recent = st.columns([1, 2])

    with col_chart:
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        st.markdown('<div class="content-box-header">Ticket Status Breakdown</div>', unsafe_allow_html=True)

        status_data = {
            "Status": ["Open", "In Progress", "Resolved", "Closed"],
            "Count": [metrics["open"], metrics["in_progress"], metrics["resolved"], metrics["closed"]]
        }
        status_df = pd.DataFrame(status_data)
        status_df = status_df[status_df["Count"] > 0]

        if not status_df.empty:
            fig = px.pie(
                status_df,
                values="Count",
                names="Status",
                hole=0.6,
                color="Status",
                color_discrete_map=config.STATUS_COLORS,
            )
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=260,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tickets submitted yet. Click **Create New Ticket** to get started.")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_recent:
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        st.markdown('<div class="content-box-header">Recent Support Requests</div>', unsafe_allow_html=True)

        recent_list = metrics["recent_tickets"]
        if recent_list:
            for t in recent_list:
                status_badge = status_badge_html(t["status"])
                priority_badge = priority_badge_html(t["priority"])
                created_str = t["created_at"].strftime("%b %d, %Y %I:%M %p") if hasattr(t["created_at"], "strftime") else str(t["created_at"])
                
                st.markdown(
                    f"""
                    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 14px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; color:#1E293B; font-size:0.95rem;">{t['ticket_number']} — {t['title']}</span>
                            <div>{status_badge} {priority_badge}</div>
                        </div>
                        <div style="font-size:0.8rem; color:#64748B; margin-top:6px;">
                            Category: <b>{t['category']}</b> &bull; Submitted: {created_str}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                """
                <div style="text-align:center; padding:30px 10px; color:#94A3B8;">
                    <div style="font-size:2rem; margin-bottom:8px;">📨</div>
                    <div style="font-weight:600; color:#475569;">No tickets yet</div>
                    <div style="font-size:0.85rem;">When you submit IT support tickets, they will appear here.</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

