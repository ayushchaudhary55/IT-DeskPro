"""
IT DeskPro - Create Support Ticket Page
Allows employees and staff to report technical issues with validations and optional attachments.
"""
import streamlit as st
import config
from utils.authentication import check_role_access, get_current_user
from utils.ticket_functions import create_ticket
from utils.validation import validate_and_save_attachment
from utils.ui_components import render_welcome_banner


def render_create_ticket_page():
    """Renders the ticket creation form with validations and attachment handling."""
    if not check_role_access(["Employee", "IT Support", "Admin"]):
        return

    current_user = get_current_user()

    render_welcome_banner(
        title="Create Support Ticket",
        subtitle="Submit a new technical request to the IT Support team. All fields marked with * are required."
    )

    with st.container():
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        st.markdown('<div class="content-box-header">Ticket Details</div>', unsafe_allow_html=True)

        with st.form("create_ticket_form", clear_on_submit=False):
            title = st.text_input(
                "Ticket Title *",
                placeholder="Brief summary of the issue (e.g., Cannot connect to VPN from home)",
                help="Enter a concise title describing the problem."
            )

            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox(
                    "Category *",
                    options=config.CATEGORIES,
                    index=0,
                    help="Select the category that best describes your issue."
                )
            with col2:
                priority = st.selectbox(
                    "Priority *",
                    options=config.PRIORITIES,
                    index=1,  # Default to Medium
                    help="Critical is reserved for company-wide or blocker incidents."
                )

            description = st.text_area(
                "Detailed Description *",
                height=150,
                placeholder="Provide steps to reproduce, error codes, device name, and any troubleshooting already attempted...",
                help="The more context you provide, the faster our IT specialists can resolve your issue."
            )

            uploaded_file = st.file_uploader(
                f"Optional Attachment (Screenshots, logs, documents - Max {config.MAX_UPLOAD_SIZE_MB}MB)",
                type=config.ALLOWED_EXTENSIONS,
                help=f"Supported file extensions: {', '.join(config.ALLOWED_EXTENSIONS)}"
            )

            submitted = st.form_submit_button(
                "🚀 Submit Ticket",
                use_container_width=True,
                type="primary"
            )

        st.markdown('</div>', unsafe_allow_html=True)

        if submitted:
            # 1. Validate attachment if provided
            attachment_path = None
            if uploaded_file is not None:
                is_file_valid, file_path_or_err, original_name = validate_and_save_attachment(uploaded_file)
                if not is_file_valid:
                    st.error(f"❌ File Attachment Error: {file_path_or_err}")
                    return
                attachment_path = file_path_or_err

            # 2. Create the ticket in MySQL
            success, ticket_num, msg = create_ticket(
                user_id=current_user["id"],
                title=title,
                description=description,
                category=category,
                priority=priority,
                attachment_path=attachment_path
            )

            if success:
                st.success(f"🎉 **Success!** Ticket **{ticket_num}** has been registered. Our IT team has been notified.")
                st.info("You can view and track updates on your ticket from the **My Tickets** tab in the sidebar.")
            else:
                st.error(f"❌ Submission Failed: {msg}")

