"""
IT DeskPro - My Tickets Page
Allows employees to view, search, filter, and track their personal tickets and resolution notes.
"""
from pathlib import Path
import streamlit as st
import config
from utils.authentication import check_role_access, get_current_user
from utils.ticket_functions import get_user_tickets, get_ticket_details, get_ticket_updates
from utils.ui_components import (
    render_welcome_banner,
    status_badge_html,
    priority_badge_html,
    role_badge_html
)


def render_my_tickets_page():
    """Renders the personal ticket history and resolution tracking view."""
    if not check_role_access(["Employee", "IT Support", "Admin"]):
        return

    current_user = get_current_user()

    render_welcome_banner(
        title="My Support Tickets",
        subtitle="Track the real-time status, IT engineer responses, and resolution notes for your tickets."
    )

    # Search & Filter Controls
    with st.container():
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        col_search, col_status, col_cat, col_prio, col_sort = st.columns([3, 2, 2, 2, 2])

        with col_search:
            search_query = st.text_input("🔍 Search", placeholder="Ticket # or keyword...")
        with col_status:
            status_filter = st.selectbox("Status", ["All"] + config.STATUSES)
        with col_cat:
            cat_filter = st.selectbox("Category", ["All"] + config.CATEGORIES)
        with col_prio:
            prio_filter = st.selectbox("Priority", ["All"] + config.PRIORITIES)
        with col_sort:
            sort_choice = st.selectbox("Sort Order", ["Newest First", "Oldest First"])
            sort_order = "DESC" if sort_choice == "Newest First" else "ASC"

        st.markdown('</div>', unsafe_allow_html=True)

    # Fetch User's Tickets
    tickets = get_user_tickets(
        user_id=current_user["id"],
        status=status_filter,
        category=cat_filter,
        priority=prio_filter,
        search=search_query,
        sort_order=sort_order
    )

    st.markdown(f"<div style='font-weight:600; color:#475569; margin-bottom:12px;'>Showing {len(tickets)} ticket(s)</div>", unsafe_allow_html=True)

    if not tickets:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:40px 20px; text-align:center; color:#64748B;">
                <div style="font-size:2.5rem; margin-bottom:10px;">🔍</div>
                <div style="font-weight:600; font-size:1.1rem; color:#1E293B;">No matching tickets found</div>
                <div style="font-size:0.88rem; margin-top:4px;">Try modifying your search keywords or resetting filters.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Render Tickets List as Clean SaaS Interactive Cards
    for t in tickets:
        status_html = status_badge_html(t["status"])
        prio_html = priority_badge_html(t["priority"])
        created_str = t["created_at"].strftime("%b %d, %Y at %I:%M %p") if hasattr(t["created_at"], "strftime") else str(t["created_at"])
        resolved_str = t["resolved_at"].strftime("%b %d, %Y at %I:%M %p") if t.get("resolved_at") and hasattr(t["resolved_at"], "strftime") else (str(t["resolved_at"]) if t.get("resolved_at") else "Pending")

        with st.expander(f"**{t['ticket_number']}** — {t['title']}  |  {t['status']}  ({t['priority']})", expanded=False):
            st.markdown(
                f"""
                <div style="margin-bottom:12px; display:flex; gap:10px; align-items:center;">
                    {status_html} {prio_html}
                    <span style="font-size:0.85rem; color:#64748B;">Category: <b>{t['category']}</b></span>
                    <span style="font-size:0.85rem; color:#64748B;">| Submitted: <b>{created_str}</b></span>
                    <span style="font-size:0.85rem; color:#64748B;">| Resolved: <b>{resolved_str}</b></span>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("##### Description")
            st.markdown(f"<div style='background:#F8FAFC; padding:12px; border-radius:6px; border:1px solid #E2E8F0; font-size:0.92rem;'>{t['description']}</div>", unsafe_allow_html=True)

            # Check attachment
            if t.get("attachment_path"):
                att_file = Path(t["attachment_path"])
                if att_file.exists():
                    st.markdown("<div style='margin-top:10px;'>", unsafe_allow_html=True)
                    try:
                        with open(att_file, "rb") as f:
                            file_bytes = f.read()
                        st.download_button(
                            label=f"📎 Download Attachment ({att_file.name.split('_', 1)[-1]})",
                            data=file_bytes,
                            file_name=att_file.name.split('_', 1)[-1],
                            key=f"att_download_{t['id']}"
                        )
                    except Exception:
                        st.info("Attachment file available on server storage.")
                    st.markdown("</div>", unsafe_allow_html=True)

            # Timeline of Resolution & History Notes
            st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
            st.markdown("##### Resolution Activity & IT Notes")

            updates = get_ticket_updates(t["id"])
            if updates:
                for up in updates:
                    up_date = up["created_at"].strftime("%b %d, %Y at %I:%M %p") if hasattr(up["created_at"], "strftime") else str(up["created_at"])
                    role_badge = role_badge_html(up["updated_by_role"])
                    status_change = f" &bull; <i>Changed status: {up['previous_status']} &rarr; <b>{up['new_status']}</b></i>" if up.get("new_status") and up.get("previous_status") else ""

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
            else:
                st.info("No updates recorded yet. Awaiting IT engineer review.")

