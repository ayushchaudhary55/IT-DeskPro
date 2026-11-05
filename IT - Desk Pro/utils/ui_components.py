"""
IT DeskPro - UI Components & Layout Utilities
Renders HTML badges, KPI cards, sidebar brand styling, and loads CSS.
"""
import streamlit as st
import config


def load_custom_css():
    """Injects the SaaS custom stylesheet into the Streamlit app."""
    css_path = config.BASE_DIR / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def status_badge_html(status: str) -> str:
    """Returns HTML for a status badge."""
    css_class = f"badge-{status.lower().replace(' ', '-')}"
    return f'<span class="badge {css_class}">{status}</span>'


def priority_badge_html(priority: str) -> str:
    """Returns HTML for a priority badge."""
    css_class = f"badge-{priority.lower()}"
    return f'<span class="badge {css_class}">{priority}</span>'


def role_badge_html(role: str) -> str:
    """Returns HTML for a user role badge."""
    return f'<span class="badge badge-role">{role}</span>'


def render_kpi_card(title: str, value: str | int, subtext: str = "", border_color: str = "#E2E8F0"):
    """Renders a styled KPI card with responsive layout."""
    card_html = f"""
    <div class="kpi-card" style="border-left: 4px solid {border_color};">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtext">{subtext}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_brand_sidebar(current_user: dict | None):
    """Renders the top branding block in the sidebar."""
    st.sidebar.markdown(
        """
        <div class="deskpro-logo-box">
            <div class="deskpro-logo-title">
                <span>🛡️</span> IT DeskPro
            </div>
            <div class="deskpro-logo-sub">Service Desk & Analytics</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if current_user:
        st.sidebar.markdown(
            f"""
            <div style="background:#1E293B; border-radius:6px; padding:10px; margin-bottom:15px; border:1px solid #334155;">
                <div style="font-size:0.75rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.04em;">Signed in as</div>
                <div style="font-weight:600; font-size:0.92rem; color:#F8FAFC; margin-top:2px;">{current_user.get('full_name', 'User')}</div>
                <div style="margin-top:4px;">
                    {role_badge_html(current_user.get('role', 'Employee'))}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_welcome_banner(title: str, subtitle: str):
    """Renders an executive SaaS header banner."""
    st.markdown(
        f"""
        <div class="welcome-banner">
            <h2 class="welcome-title">{title}</h2>
            <p class="welcome-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

