"""
IT DeskPro - IT Support & Admin Executive Dashboard
Displays enterprise KPI cards, attention-required tickets, and operational charts from MySQL.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import config
from utils.authentication import check_role_access, get_current_user
from utils.ticket_functions import get_admin_dashboard_metrics, get_all_tickets
from utils.ui_components import (
    render_kpi_card,
    render_welcome_banner,
    status_badge_html,
    priority_badge_html
)


def render_admin_dashboard():
    """Renders the executive operations dashboard for IT Support & Admins."""
    if not check_role_access(["IT Support", "Admin"]):
        return

    current_user = get_current_user()
    metrics = get_admin_dashboard_metrics()

    render_welcome_banner(
        title=f"IT Service Desk Operations 🚀",
        subtitle=f"Real-time ticket volume, queue health, SLA performance, and priority response tracking."
    )

    # 6 KPI Cards Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        render_kpi_card("Total Tickets", metrics["total"], "All time logged", "#1E293B")
    with c2:
        render_kpi_card("Open Queue", metrics["open"], "Awaiting response", "#2563EB")
    with c3:
        render_kpi_card("In Progress", metrics["in_progress"], "Under investigation", "#D97706")
    with c4:
        render_kpi_card("Resolved", metrics["resolved"] + metrics["closed"], "Completed tickets", "#10B981")
    with c5:
        render_kpi_card("Critical Active", metrics["critical_active"], "High SLA impact", "#EF4444")
    with c6:
        render_kpi_card("Avg Resolution", metrics["avg_resolution_time"], "SLA resolution", "#6366F1")

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # Tickets Requiring Attention Banner / List
    st.markdown('<div class="content-box">', unsafe_allow_html=True)
    st.markdown('<div class="content-box-header">⚡ Tickets Requiring Immediate Attention (Critical & High Active)</div>', unsafe_allow_html=True)

    attention_list = metrics["attention_tickets"]
    if attention_list:
        cols = st.columns(len(attention_list) if len(attention_list) <= 3 else 3)
        for idx, item in enumerate(attention_list):
            target_col = cols[idx % 3]
            with target_col:
                prio_badge = priority_badge_html(item["priority"])
                status_badge = status_badge_html(item["status"])
                created_str = item["created_at"].strftime("%b %d, %I:%M %p") if hasattr(item["created_at"], "strftime") else str(item["created_at"])
                st.markdown(
                    f"""
                    <div style="background:#FFF1F2; border:1px solid #FECDD3; border-radius:8px; padding:12px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; color:#9F1239; font-size:0.9rem;">{item['ticket_number']}</span>
                            <div>{prio_badge} {status_badge}</div>
                        </div>
                        <div style="font-weight:600; color:#1E293B; margin-top:4px; font-size:0.9rem;">{item['title']}</div>
                        <div style="font-size:0.78rem; color:#64748B; margin-top:4px;">
                            Submitted by: <b>{item['employee_name']}</b><br>
                            Created: {created_str}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.success("✅ Great job! No critical or high-priority tickets are currently awaiting attention.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Distribution Charts Row
    st.markdown("### Operational Queue Breakdowns")
    chart_col1, chart_col2, chart_col3 = st.columns(3)

    # Query all tickets for breakdown charts
    all_tickets = get_all_tickets()
    if all_tickets:
        df = pd.DataFrame(all_tickets)

        with chart_col1:
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.markdown('<div class="content-box-header">Queue Status Distribution</div>', unsafe_allow_html=True)
            st_counts = df["status"].value_counts().reset_index()
            st_counts.columns = ["Status", "Count"]
            fig_st = px.pie(
                st_counts,
                values="Count",
                names="Status",
                hole=0.55,
                color="Status",
                color_discrete_map=config.STATUS_COLORS,
            )
            fig_st.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_st, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_col2:
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.markdown('<div class="content-box-header">Tickets by Priority</div>', unsafe_allow_html=True)
            prio_order = ["Low", "Medium", "High", "Critical"]
            prio_counts = df["priority"].value_counts().reindex(prio_order, fill_value=0).reset_index()
            prio_counts.columns = ["Priority", "Count"]
            fig_pr = px.bar(
                prio_counts,
                x="Priority",
                y="Count",
                text="Count",
                color="Priority",
                color_discrete_map=config.PRIORITY_COLORS
            )
            fig_pr.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#FFFFFF",
                xaxis=dict(title=None, showgrid=False),
                yaxis=dict(title=None, showgrid=True, gridcolor="#F1F5F9"),
                showlegend=False
            )
            st.plotly_chart(fig_pr, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_col3:
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.markdown('<div class="content-box-header">Category Volume</div>', unsafe_allow_html=True)
            cat_counts = df["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            fig_cat = px.bar(
                cat_counts,
                x="Category",
                y="Count",
                text="Count",
                color="Category",
                color_discrete_sequence=["#1E293B", "#2563EB", "#0284C7", "#0D9488", "#D97706", "#64748B"]
            )
            fig_cat.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#FFFFFF",
                xaxis=dict(title=None, showgrid=False),
                yaxis=dict(title=None, showgrid=True, gridcolor="#F1F5F9"),
                showlegend=False
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No tickets currently logged in the system.")

    # Recent Tickets Table
    st.markdown('<div class="content-box">', unsafe_allow_html=True)
    st.markdown('<div class="content-box-header">Recent Organization-Wide Requests</div>', unsafe_allow_html=True)

    recent_all = metrics["recent_tickets"]
    if recent_all:
        table_rows = []
        for r in recent_all:
            created_str = r["created_at"].strftime("%b %d, %Y %I:%M %p") if hasattr(r["created_at"], "strftime") else str(r["created_at"])
            table_rows.append({
                "Ticket #": r["ticket_number"],
                "Employee": r["employee_name"],
                "Title": r["title"],
                "Category": r["category"],
                "Priority": r["priority"],
                "Status": r["status"],
                "Created At": created_str,
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No recent tickets to display.")

    st.markdown('</div>', unsafe_allow_html=True)

