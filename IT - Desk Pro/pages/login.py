"""
IT DeskPro - Authentication & Login Page
Handles employee and IT staff login, new account registration, and demo account shortcuts.
"""
import streamlit as st
import database
from utils.authentication import authenticate_user, register_user, login_user_session
from utils.ui_components import render_welcome_banner


def render_login_page():
    """Renders the login and registration interface."""
    # Test DB status first to give helpful notice if offline
    db_ok, db_msg = database.test_connection()
    if not db_ok:
        st.error(f"⚠️ **Database Alert**: Cannot reach MySQL server ({db_msg}). Please ensure MySQL service is running.")

    col_center = st.columns([1, 2, 1])[1]

    with col_center:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 20px; margin-bottom: 25px;">
                <div style="font-size: 2.8rem; margin-bottom: 8px;">🛡️</div>
                <h1 style="font-size: 1.85rem; font-weight: 700; color: #0F172A; margin: 0;">IT DeskPro</h1>
                <p style="font-size: 0.95rem; color: #64748B; margin-top: 6px;">Enterprise Service Desk & Ticket Analytics</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        tab_login, tab_register, tab_demo = st.tabs(["🔐 Sign In", "📝 Register Employee", "⚡ Demo Credentials"])

        # Tab 1: Sign In
        with tab_login:
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Work Email", placeholder="name@company.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                login_submit = st.form_submit_button("Sign In to DeskPro", type="primary", use_container_width=True)

            if login_submit:
                if not email or not password:
                    st.error("Please enter both your work email and password.")
                else:
                    success, msg, user_data = authenticate_user(email, password)
                    if success and user_data:
                        login_user_session(user_data)
                        st.success(f"Welcome back, {user_data['full_name']}!")
                        # Set default page based on role
                        if user_data["role"] in ["IT Support", "Admin"]:
                            st.session_state["current_page"] = "Admin Dashboard"
                        else:
                            st.session_state["current_page"] = "Employee Dashboard"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

            st.markdown('</div>', unsafe_allow_html=True)

        # Tab 2: Register New Employee Account
        with tab_register:
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.88rem; color:#64748B;'>New employee? Register your corporate profile below:</p>", unsafe_allow_html=True)
            with st.form("register_form"):
                reg_name = st.text_input("Full Name *", placeholder="Jane Doe")
                reg_email = st.text_input("Company Email *", placeholder="jane.doe@company.com")
                reg_pass = st.text_input("Choose Password (min 6 chars) *", type="password")
                reg_pass2 = st.text_input("Confirm Password *", type="password")
                reg_submit = st.form_submit_button("Create Employee Account", type="primary", use_container_width=True)

            if reg_submit:
                if reg_pass != reg_pass2:
                    st.error("Passwords do not match.")
                else:
                    reg_ok, reg_msg, new_id = register_user(
                        full_name=reg_name,
                        email=reg_email,
                        password=reg_pass,
                        role="Employee"
                    )
                    if reg_ok:
                        st.success("✅ Account created successfully! Please sign in using the 'Sign In' tab.")
                    else:
                        st.error(f"❌ {reg_msg}")

            st.markdown('</div>', unsafe_allow_html=True)

        # Tab 3: Demo Accounts Reference & Quick Fill
        with tab_demo:
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.markdown(
                """
                <div style="font-size:0.85rem; color:#475569; line-height:1.7;">
                    <b>Sample Demo Logins (Default password for all demo accounts is <code>Password123!</code>):</b>
                    <ul style="padding-left: 20px; margin-top: 8px;">
                        <li><b>Admin:</b> <code>alex.rivera@deskpro.local</code></li>
                        <li><b>IT Support:</b> <code>sarah.chen@deskpro.local</code></li>
                        <li><b>IT Support:</b> <code>marcus.vance@deskpro.local</code></li>
                        <li><b>Employee:</b> <code>emily.watson@deskpro.local</code></li>
                        <li><b>Employee:</b> <code>david.kim@deskpro.local</code></li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown("<div style='font-size:0.8rem; color:#64748B;'>Need demo records? Run <code>python database/seed_demo_data.py</code> in terminal to generate realistic accounts and tickets.</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

