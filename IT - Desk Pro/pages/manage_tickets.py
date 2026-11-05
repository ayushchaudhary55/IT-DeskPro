"""
IT DeskPro - Manage Tickets (IT Support / Admin)
Full lifecycle ticket resolution, priority adjustment, status transition, and audit trail logging.
"""
from pathlib import Path
import streamlit as st
import pandas as pd
import config
from utils.authentication import check_role_access, get_current_user
from utils.ticket_functions import (
    get_all_tickets,
    get_ticket_details,
    get_ticket_updates,
    update_ticket_status_and_notes
)
from utils.ui_components import (
    render_welcome_banner,
    status_badge_html,
    priority_badge_html,
    role_badge_html
)


def render_manage_tickets_page():
    """Renders the comprehensive ticket resolution and management console."""
    if not check_role_access(["IT Support", "Admin"]):
        return

    current_user = get_current_user()

    render_welcome_banner(
        title="Manage IT Support Tickets",
        subtitle="Review employee requests, adjust priorities, transition status, and record resolution notes."
    )

    # Search & Filter Controls
    with st.container():
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        col_search, col_status, col_cat, col_prio, col_sort = st.columns([3, 2, 2, 2, 2])

        with col_search:
            search_query = st.text_input("🔍 Search", placeholder="Ticket #, title, employee name...")
        with col_status:
            status_filter = st.selectbox("Status", ["All"] + config.STATUSES, key="mgmt_status")
        with col_cat:
            cat_filter = st.selectbox("Category", ["All"] + config.CATEGORIES, key="mgmt_cat")
        with col_prio:
            prio_filter = st.selectbox("Priority", ["All"] + config.PRIORITIES, key="mgmt_prio")
        with col_sort:
            sort_choice = st.selectbox("Sort Order", ["Newest First", "Oldest First"], key="mgmt_sort")
            sort_order = "DESC" if sort_choice == "Newest First" else "ASC"

        st.markdown('</div>', unsafe_allow_html=True)

    # Fetch Tickets
    tickets = get_all_tickets(
        status=status_filter,
        category=cat_filter,
        priority=prio_filter,
        search=search_query,
        sort_order=sort_order
    )

    st.markdown(f"<div style='font-weight:600; color:#475569; margin-bottom:12px;'>Found {len(tickets)} total ticket(s)</div>", unsafe_allow_html=True)

    if not tickets:
        st.info("No tickets match the selected filter criteria.")
        return

    # Two column layout: Left side ticket list / selector, Right side full update & resolution panel
    col_list, col_action = st.columns([1, 1])

    # Session state key to remember selected ticket
    if "selected_ticket_id" not in st.session_state or not any(t["id"] == st.session_state["selected_ticket_id"] for t in tickets):
        st.session_state["selected_ticket_id"] = tickets[0]["id"]

    with col_list:
        st.markdown("##### Select Ticket to Review")
        for t in tickets:
            is_selected = (t["id"] == st.session_state["selected_ticket_id"])
            border_style = "2px solid #2563EB" if is_selected else "1px solid #E2E8F0"
            bg_style = "#EFF6FF" if is_selected else "#FFFFFF"

            status_html = status_badge_html(t["status"])
            prio_html = priority_badge_html(t["priority"])
            created_str = t["created_at"].strftime("%b %d, %Y %I:%M %p") if hasattr(t["created_at"], "strftime") else str(t["created_at"])

            st.markdown(
                f"""
                <div style="background:{bg_style}; border:{border_style}; border-radius:8px; padding:12px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; color:#1E293B;">{t['ticket_number']}</span>
                        <div>{status_html} {prio_html}</div>
                    </div>
                    <div style="font-weight:600; color:#334155; margin-top:4px; font-size:0.92rem;">{t['title']}</div>
                    <div style="font-size:0.78rem; color:#64748B; margin-top:4px;">
                        Employee: <b>{t['employee_name']}</b> ({t['employee_email']}) &bull; {created_str}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"Manage {t['ticket_number']}", key=f"btn_sel_{t['id']}", use_container_width=True):
                st.session_state["selected_ticket_id"] = t["id"]
                st.rerun()

    # Detail and Management Action Panel
    with col_action:
        selected_id = st.session_state["selected_ticket_id"]
        ticket = get_ticket_details(selected_id)

        if not ticket:
            st.warning("Please select a ticket from the left panel.")
            return

        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="content-box-header">Ticket #{ticket["ticket_number"]} Resolution Console</div>', unsafe_allow_html=True)

        created_str = ticket["created_at"].strftime("%b %d, %Y at %I:%M %p") if hasattr(ticket["created_at"], "strftime") else str(ticket["created_at"])
        updated_str = ticket["updated_at"].strftime("%b %d, %Y at %I:%M %p") if hasattr(ticket["updated_at"], "strftime") else str(ticket["updated_at"])
        resolved_str = ticket["resolved_at"].strftime("%b %d, %Y at %I:%M %p") if ticket.get("resolved_at") and hasattr(ticket["resolved_at"], "strftime") else "Not Resolved"

        st.markdown(
            f"""
            <div style="font-size:0.85rem; color:#475569; line-height:1.6; margin-bottom:15px; background:#F8FAFC; padding:12px; border-radius:6px; border:1px solid #E2E8F0;">
                <b>Employee:</b> {ticket['employee_name']} ({ticket['employee_email']})<br>
                <b>Category:</b> {ticket['category']} &bull; <b>Current Priority:</b> {ticket['priority']} &bull; <b>Status:</b> {ticket['status']}<br>
                <b>Created:</b> {created_str}<br>
                <b>Last Updated:</b> {updated_str}<br>
                <b>Resolved At:</b> {resolved_str}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("##### Issue Description")
        st.info(ticket["description"])

        # Check attachment
        if ticket.get("attachment_path"):
            att_file = Path(ticket["attachment_path"])
            if att_file.exists():
                try:
                    with open(att_file, "rb") as f:
                        data = f.read()
                    st.download_button(
                        f"📎 Download Attachment ({att_file.name.split('_', 1)[-1]})",
                        data=data,
                        file_name=att_file.name.split('_', 1)[-1],
                        key=f"att_mgmt_dl_{ticket['id']}"
                    )
                except Exception:
                    st.text("Attachment file exists on server.")

        st.markdown("---")
        st.markdown("##### Update Ticket Status & Resolution Notes")

        # Form for modifying ticket state
        with st.form(f"mgmt_update_form_{ticket['id']}"):
            fcol1, fcol2 = st.columns(2)
            with fcol1:
                cur_status_idx = config.STATUSES.index(ticket["status"]) if ticket["status"] in config.STATUSES else 0
                new_status = st.selectbox("Update Status", config.STATUSES, index=cur_status_idx)
            with fcol2:
                cur_prio_idx = config.PRIORITIES.index(ticket["priority"]) if ticket["priority"] in config.PRIORITIES else 0
                new_priority = st.selectbox("Update Priority", config.PRIORITIES, index=cur_prio_idx)

            note_placeholder = (
                "Document resolution steps, root cause, or internal updates..."
                if new_status == "Resolved"
                else "Add update note or instructions for the employee..."
            )
            update_note = st.text_area("Resolution / Internal Note *", placeholder=note_placeholder, height=100)

            save_btn = st.form_submit_button("💾 Save Update & Log Audit Entry", type="primary", use_container_width=True)

        if save_btn:
            if not update_note.strip():
                st.error("❌ Please provide an update note explaining this modification.")
            else:
                ok, msg = update_ticket_status_and_notes(
                    ticket_id=ticket["id"],
                    updated_by_user_id=current_user["id"],
                    new_status=new_status,
                    new_priority=new_priority,
                    update_note=update_note
                )
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

        # Audit Trail Timeline
        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        st.markdown("##### Audit Trail & History")
        updates = get_ticket_updates(ticket["id"])
        if updates:
            for up in updates:
                up_date = up["created_at"].strftime("%b %d, %Y %I:%M %p") if hasattr(up["created_at"], "strftime") else str(up["created_at"])
                role_badge = role_badge_html(up["updated_by_role"])
                status_change = f" &bull; <i>{up['previous_status']} &rarr; <b>{up['new_status']}</b></i>" if up.get("new_status") and up.get("previous_status") else ""
                st.markdown(
                    f"""
                    <div class="timeline-item">
                        <div class="timeline-header">
                            <div><b>{up['updated_by_name']}</b> {role_badge} {status_change}</div>
                            <div>{up_date}</div>
                        </div>
                        <div class="timeline-body">{up['update_note']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)

