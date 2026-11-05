"""
IT DeskPro - User Profile & Account Settings
View account details, update display name, and securely change password.
"""
import streamlit as st
from utils.authentication import (
    check_role_access,
    get_current_user,
    get_user_by_id,
    update_user_profile,
    change_user_password
)
from utils.ui_components import render_welcome_banner, role_badge_html


def render_profile_page():
    """Renders the personal profile and security management view."""
    if not check_role_access(["Employee", "IT Support", "Admin"]):
        return

    current_user = get_current_user()
    db_user = get_user_by_id(current_user["id"])
    if not db_user:
        db_user = current_user

    render_welcome_banner(
        title="My Account Settings",
        subtitle="Manage your personal details, verify account credentials, and update your password."
    )

    col_profile, col_security = st.columns(2)

    with col_profile:
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        st.markdown('<div class="content-box-header">Profile Information</div>', unsafe_allow_html=True)

        created_str = (
            db_user["created_at"].strftime("%B %d, %Y at %I:%M %p")
            if hasattr(db_user["created_at"], "strftime")
            else str(db_user["created_at"])
        )

        st.markdown(
            f"""
            <div style="margin-bottom:15px; font-size:0.88rem; color:#475569; line-height:1.8;">
                <b>Email:</b> {db_user['email']} <br>
                <b>Role:</b> {role_badge_html(db_user['role'])} <span style="font-size:0.75rem; color:#94A3B8;">(Managed by IT Administration)</span><br>
                <b>Account Created:</b> {created_str}
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("update_profile_form"):
            new_name = st.text_input("Display Name", value=db_user["full_name"])
            save_name_btn = st.form_submit_button("Update Display Name", type="primary")

        if save_name_btn:
            ok, msg = update_user_profile(db_user["id"], new_name)
            if ok:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_security:
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        st.markdown('<div class="content-box-header">Change Password</div>', unsafe_allow_html=True)

        with st.form("change_password_form"):
            curr_pass = st.text_input("Current Password *", type="password")
            new_pass = st.text_input("New Password (min 6 characters) *", type="password")
            confirm_pass = st.text_input("Confirm New Password *", type="password")

            save_pwd_btn = st.form_submit_button("Update Password", type="primary")

        if save_pwd_btn:
            if not curr_pass:
                st.error("Please enter your current password.")
            elif not new_pass or len(new_pass) < 6:
                st.error("New password must be at least 6 characters long.")
            elif new_pass != confirm_pass:
                st.error("New password and confirmation do not match.")
            else:
                ok, msg = change_user_password(db_user["id"], curr_pass, new_pass)
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

        st.markdown('</div>', unsafe_allow_html=True)

