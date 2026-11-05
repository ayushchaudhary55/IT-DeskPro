"""
IT DeskPro - Analytics & Reporting Engine
Transforms MySQL ticket data with Pandas and renders high-fidelity Plotly SaaS charts.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import database
import config


def get_analytics_dataframe(start_date=None, end_date=None) -> pd.DataFrame:
    """
    Fetches tickets from MySQL and returns a clean, typed Pandas DataFrame.
    Supports optional date filtering by ticket creation date.
    """
    conditions = ["1=1"]
    params = []

    if start_date:
        conditions.append("DATE(t.created_at) >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("DATE(t.created_at) <= %s")
        params.append(end_date)

    sql = f"""
        SELECT 
            t.id,
            t.ticket_number,
            u.full_name AS employee_name,
            u.email AS employee_email,
            t.title,
            t.description,
            t.category,
            t.priority,
            t.status,
            t.created_at,
            t.updated_at,
            t.resolved_at,
            CASE 
                WHEN t.resolved_at IS NOT NULL 
                THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) 
                ELSE NULL 
            END AS resolution_minutes
        FROM tickets t
        INNER JOIN users u ON t.user_id = u.id
        WHERE {' AND '.join(conditions)}
        ORDER BY t.created_at DESC;
    """
    rows = database.fetch_all(sql, params)
    if not rows:
        return pd.DataFrame(columns=[
            "id", "ticket_number", "employee_name", "employee_email",
            "title", "description", "category", "priority", "status",
            "created_at", "updated_at", "resolved_at", "resolution_minutes"
        ])

    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["updated_at"] = pd.to_datetime(df["updated_at"])
    df["resolved_at"] = pd.to_datetime(df["resolved_at"])
    df["resolution_hours"] = df["resolution_minutes"].apply(
        lambda m: round(m / 60.0, 1) if pd.notnull(m) and m >= 0 else None
    )
    return df


def calculate_kpis(df: pd.DataFrame) -> dict:
    """Computes summary KPI indicators from the DataFrame."""
    if df.empty:
        return {
            "total_tickets": 0,
            "resolved_count": 0,
            "resolution_rate": "0%",
            "avg_resolution_time": "N/A",
            "critical_tickets": 0
        }

    total = len(df)
    resolved = len(df[df["status"].isin(["Resolved", "Closed"])])
    rate = round((resolved / total) * 100, 1) if total > 0 else 0
    critical = len(df[df["priority"] == "Critical"])

    resolved_df = df[df["resolution_hours"].notnull()]
    if not resolved_df.empty and resolved_df["resolution_hours"].mean() > 0:
        avg_h = round(resolved_df["resolution_hours"].mean(), 1)
        if avg_h >= 24:
            avg_res_str = f"{round(avg_h / 24, 1)} days"
        else:
            avg_res_str = f"{avg_h} hrs"
    else:
        avg_res_str = "N/A"

    return {
        "total_tickets": total,
        "resolved_count": resolved,
        "resolution_rate": f"{rate}%",
        "avg_resolution_time": avg_res_str,
        "critical_tickets": critical
    }


def plot_tickets_by_category(df: pd.DataFrame) -> go.Figure:
    """Renders a polished SaaS bar chart of tickets grouped by Category."""
    if df.empty:
        return _empty_chart("No ticket data available for category analysis")

    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]

    fig = px.bar(
        cat_counts,
        x="Category",
        y="Count",
        text="Count",
        color="Category",
        color_discrete_sequence=["#1E293B", "#2563EB", "#0284C7", "#0D9488", "#D97706", "#64748B"],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Tickets: %{y}<extra></extra>",
        marker=dict(line=dict(width=0))
    )
    fig.update_layout(
        title=dict(text="Tickets by Category", font=dict(size=16, color="#0F172A", family="Inter, sans-serif")),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(showgrid=False, title=None, tickfont=dict(color="#475569")),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title=None, tickfont=dict(color="#475569")),
        showlegend=False,
        height=320,
    )
    return fig


def plot_tickets_by_status(df: pd.DataFrame) -> go.Figure:
    """Renders a donut chart of tickets by Status."""
    if df.empty:
        return _empty_chart("No status data available")

    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    color_map = config.STATUS_COLORS

    fig = px.pie(
        status_counts,
        values="Count",
        names="Status",
        hole=0.55,
        color="Status",
        color_discrete_map=color_map,
    )
    fig.update_traces(
        textinfo="percent+value",
        textposition="inside",
        hoverinfo="label+value+percent",
        marker=dict(line=dict(color="#FFFFFF", width=2))
    )
    fig.update_layout(
        title=dict(text="Tickets by Status", font=dict(size=16, color="#0F172A", family="Inter, sans-serif")),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        height=320,
    )
    return fig


def plot_tickets_by_priority(df: pd.DataFrame) -> go.Figure:
    """Renders a bar chart of tickets grouped by Priority with matching SaaS color cues."""
    if df.empty:
        return _empty_chart("No priority data available")

    priority_order = ["Low", "Medium", "High", "Critical"]
    priority_counts = df["priority"].value_counts().reindex(priority_order, fill_value=0).reset_index()
    priority_counts.columns = ["Priority", "Count"]

    fig = px.bar(
        priority_counts,
        x="Priority",
        y="Count",
        text="Count",
        color="Priority",
        color_discrete_map=config.PRIORITY_COLORS,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>Priority: %{x}</b><br>Tickets: %{y}<extra></extra>"
    )
    fig.update_layout(
        title=dict(text="Tickets by Priority", font=dict(size=16, color="#0F172A", family="Inter, sans-serif")),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(showgrid=False, title=None, tickfont=dict(color="#475569")),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title=None, tickfont=dict(color="#475569")),
        showlegend=False,
        height=320,
    )
    return fig


def plot_monthly_trend(df: pd.DataFrame) -> go.Figure:
    """Renders a monthly ticket creation trend line chart."""
    if df.empty:
        return _empty_chart("No trend data available")

    df_trend = df.copy()
    df_trend["YearMonth"] = df_trend["created_at"].dt.to_period("M").dt.to_timestamp()
    trend_counts = df_trend.groupby("YearMonth").size().reset_index(name="Count")
    trend_counts = trend_counts.sort_values("YearMonth")

    fig = px.line(
        trend_counts,
        x="YearMonth",
        y="Count",
        markers=True,
        line_shape="spline",
    )
    fig.update_traces(
        line=dict(color="#2563EB", width=3),
        marker=dict(size=8, color="#1E293B", symbol="circle"),
        hovertemplate="Month: %{x|%b %Y}<br>Tickets: %{y}<extra></extra>"
    )
    fig.update_layout(
        title=dict(text="Monthly Ticket Creation Trend", font=dict(size=16, color="#0F172A", family="Inter, sans-serif")),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(
            showgrid=False,
            title=None,
            tickformat="%b %Y",
            tickfont=dict(color="#475569")
        ),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Tickets Created", tickfont=dict(color="#475569")),
        height=320,
    )
    return fig


def _empty_chart(message: str) -> go.Figure:
    """Helper that returns an elegant empty state placeholder chart."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"📊 {message}",
        showarrow=False,
        font=dict(size=14, color="#94A3B8", family="Inter, sans-serif"),
        xref="paper", yref="paper",
        x=0.5, y=0.5
    )
    fig.update_layout(
        plot_bgcolor="#F8FAFC",
        paper_bgcolor="#F8FAFC",
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig

