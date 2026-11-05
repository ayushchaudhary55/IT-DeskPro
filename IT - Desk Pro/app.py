"""
IT DeskPro - Main Application Entry Point
Enterprise Service Desk & Ticket Analytics Built with Streamlit, MySQL, Pandas, Plotly & Bcrypt.
"""
import streamlit as st
import database
from utils.authentication import is_logged_in, get_current_user, logout_user_session
from utils.ui_components import load_custom_css, render_brand_sidebar

# Import Page Views
from pages.login import render_login_page
from pages.employee_dashboard import render_employee_dashboard
from pages.create_ticket import render_create_ticket_page
from pages.my_tickets import render_my_tickets_page
from pages.admin_dashboard import render_admin_dashboard
from pages.manage_tickets import render_manage_tickets_page
from pages.analytics import render_analytics_page
from pages.profile import render_profile_page

# 1. Page Configuration
st.set_page_config(
    page_title="IT DeskPro — Service Desk & Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom SaaS Styles
load_custom_css()

# 3. Ensure Database Schema is Ready
try:
    database.init_database_if_needed()
except Exception as ex:
    st.error(f"⚠️ Database initialization notice: {ex}")

# 4. Authentication Check
if not is_logged_in():
    # Render Login & Registration View
    render_login_page()
else:
    current_user = get_current_user()
    user_role = current_user.get("role", "Employee")

    # Render Sidebar Brand & Identity
    render_brand_sidebar(current_user)

    # Define Navigation Menu based on User Role
    if user_role == "Employee":
        nav_options = [
            "📊 Dashboard",
            "➕ Create Ticket",
            "📋 My Tickets",
            "👤 Profile & Security",
        ]
        page_mapping = {
            "📊 Dashboard": "Employee Dashboard",
            "➕ Create Ticket": "Create Ticket",
            "📋 My Tickets": "My Tickets",
            "👤 Profile & Security": "Profile",
        }
    else:  # "IT Support" or "Admin"
        nav_options = [
            "📊 Operations Dashboard",
            "🛠️ Manage Tickets",
            "➕ Create Ticket",
            "📋 My Tickets",
            "📈 Analytics & Reports",
            "👤 Profile & Security",
        ]
        page_mapping = {
            "📊 Operations Dashboard": "Admin Dashboard",
            "🛠️ Manage Tickets": "Manage Tickets",
            "➕ Create Ticket": "Create Ticket",
            "📋 My Tickets": "My Tickets",
            "📈 Analytics & Reports": "Analytics",
            "👤 Profile & Security": "Profile",
        }

    # Initialize current page state
    reverse_mapping = {v: k for k, v in page_mapping.items()}
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Employee Dashboard" if user_role == "Employee" else "Admin Dashboard"

    # Match selection with session state
    default_nav_label = reverse_mapping.get(st.session_state["current_page"], nav_options[0])
    selected_nav = st.sidebar.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(default_nav_label) if default_nav_label in nav_options else 0,
        label_visibility="collapsed"
    )
    st.session_state["current_page"] = page_mapping[selected_nav]

    # Sidebar Logout Button
    st.sidebar.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        logout_user_session()

    # Route to Requested Page with Server-Side Role Enforcement
    page = st.session_state["current_page"]

    if page == "Employee Dashboard":
        render_employee_dashboard()
    elif page == "Create Ticket":
        render_create_ticket_page()
    elif page == "My Tickets":
        render_my_tickets_page()
    elif page == "Admin Dashboard":
        if user_role not in ["IT Support", "Admin"]:
            st.error("⛔ Access Denied: You do not have permission to view the IT Support dashboard.")
        else:
            render_admin_dashboard()
    elif page == "Manage Tickets":
        if user_role not in ["IT Support", "Admin"]:
            st.error("⛔ Access Denied: You do not have permission to manage IT tickets.")
        else:
            render_manage_tickets_page()
    elif page == "Analytics":
        if user_role not in ["IT Support", "Admin"]:
            st.error("⛔ Access Denied: You do not have permission to view organizational analytics.")
        else:
            render_analytics_page()
    elif page == "Profile":
        render_profile_page()
    else:
        render_employee_dashboard()

