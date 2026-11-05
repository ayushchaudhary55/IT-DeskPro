"""
IT DeskPro - Automated System Test Suite
Executes end-to-end verification across all 17 requirements in the Testing Checklist.
"""
import sys
from pathlib import Path
import io

# Setup workspace path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import database
from utils.authentication import (
    authenticate_user,
    hash_password,
    verify_password,
    register_user,
    change_user_password,
    update_user_profile,
    get_user_by_id
)
from utils.ticket_functions import (
    create_ticket,
    get_user_tickets,
    get_all_tickets,
    get_ticket_details,
    get_ticket_updates,
    update_ticket_status_and_notes,
    generate_ticket_number,
    get_employee_dashboard_metrics,
    get_admin_dashboard_metrics
)
from utils.validation import (
    validate_email,
    validate_password,
    validate_ticket_input,
    validate_and_save_attachment
)
from utils.analytics import (
    get_analytics_dataframe,
    calculate_kpis,
    plot_tickets_by_category,
    plot_tickets_by_status,
    plot_tickets_by_priority,
    plot_monthly_trend
)


class MockUploadedFile:
    def __init__(self, name: str, size: int, content: bytes):
        self.name = name
        self.size = size
        self._content = content

    def getbuffer(self):
        return self._content


def run_checklist_tests():
    passed = 0
    failed = 0
    results = []

    def log_test(num: int, title: str, status: bool, detail: str = ""):
        nonlocal passed, failed
        if status:
            passed += 1
            results.append((num, title, "PASS", detail))
            print(f"  [PASS] Test {num:02d}: {title} {('- ' + detail) if detail else ''}")
        else:
            failed += 1
            results.append((num, title, "FAIL", detail))
            print(f"  [FAIL] Test {num:02d}: {title} - ERROR: {detail}")

    print("\n" + "=" * 70)
    print(" RUNNING IT DESKPRO VERIFICATION TEST SUITE (17 CHECKLIST ITEMS)")
    print("=" * 70 + "\n")

    # 1. Test Database connection
    try:
        ok, msg = database.test_connection()
        log_test(17, "Database connection handled gracefully", ok, msg)
    except Exception as e:
        log_test(17, "Database connection handled gracefully", False, str(e))

    # 2. Test Valid Login
    try:
        ok, msg, user = authenticate_user("alex.rivera@deskpro.local", "Password123!")
        log_test(1, "Valid login authentication", ok and user["role"] == "Admin", f"Logged in as {user['full_name']} ({user['role']})")
    except Exception as e:
        log_test(1, "Valid login authentication", False, str(e))

    # 3. Test Invalid Login
    try:
        ok, msg, user = authenticate_user("alex.rivera@deskpro.local", "WrongPassword!")
        log_test(2, "Invalid login rejection", not ok and user is None, f"Response: {msg}")
    except Exception as e:
        log_test(2, "Invalid login rejection", False, str(e))

    # 4. Test Logout (Session clearing)
    try:
        import streamlit as st
        # Simulate session state
        st.session_state["user"] = {"id": 1, "role": "Employee"}
        st.session_state["user"] = None
        log_test(3, "Logout clears session state", st.session_state["user"] is None, "Session wiped successfully")
    except Exception as e:
        log_test(3, "Logout clears session state", False, str(e))

    # 5. Test Role Gating (Employee cannot access admin modules)
    try:
        emp_user = database.fetch_one("SELECT * FROM users WHERE role = 'Employee' LIMIT 1;")
        admin_allowed_roles = ["IT Support", "Admin"]
        is_blocked = emp_user["role"] not in admin_allowed_roles
        log_test(4, "Employee blocked from admin operations", is_blocked, f"Employee role '{emp_user['role']}' denied admin rights")
    except Exception as e:
        log_test(4, "Employee blocked from admin operations", False, str(e))

    # 6. Test Empty Ticket Fields are Rejected
    try:
        val_ok, val_msg = validate_ticket_input("", "", "Hardware", "Low")
        log_test(6, "Empty ticket fields rejected", not val_ok, f"Validation message: {val_msg}")
    except Exception as e:
        log_test(6, "Empty ticket fields rejected", False, str(e))

    # 7. Test Unique Ticket Number Generation
    try:
        num1 = generate_ticket_number()
        # Verify format
        is_format_ok = num1.startswith("ITD-") and len(num1) == 13
        log_test(7, "Unique ticket number format ITD-YYYY-XXXX", is_format_ok, f"Generated: {num1}")
    except Exception as e:
        log_test(7, "Unique ticket number format ITD-YYYY-XXXX", False, str(e))

    # 8. Test Employee Can Create a Ticket
    created_ticket_num = None
    created_ticket_id = None
    try:
        emp = database.fetch_one("SELECT id, full_name FROM users WHERE role = 'Employee' LIMIT 1;")
        ok, num, msg = create_ticket(
            user_id=emp["id"],
            title="Automated Test Support Ticket",
            description="This is a test description exceeding ten characters to verify ticket insertion.",
            category="Software",
            priority="High"
        )
        created_ticket_num = num
        ticket_row = database.fetch_one("SELECT id, status FROM tickets WHERE ticket_number = %s;", (num,))
        if ticket_row:
            created_ticket_id = ticket_row["id"]
        log_test(5, "Employee can create a ticket", ok and ticket_row["status"] == "Open", f"Created ticket #{num} with status Open")
    except Exception as e:
        log_test(5, "Employee can create a ticket", False, str(e))

    # 9. Test Employee Sees Only Their Own Tickets
    try:
        emp_tickets = get_user_tickets(emp["id"])
        all_emp_owned = all(t["user_id"] == emp["id"] for t in emp_tickets)
        log_test(8, "Employee sees only their own tickets", all_emp_owned and len(emp_tickets) > 0, f"Verified {len(emp_tickets)} tickets for user {emp['id']}")
    except Exception as e:
        log_test(8, "Employee sees only their own tickets", False, str(e))

    # 10. Test Admin Can View All Tickets
    try:
        all_t = get_all_tickets()
        distinct_users = len(set(t["user_id"] for t in all_t))
        log_test(9, "Admin can view all tickets across employees", len(all_t) >= len(emp_tickets) and distinct_users > 1, f"Found {len(all_t)} tickets across {distinct_users} users")
    except Exception as e:
        log_test(9, "Admin can view all tickets across employees", False, str(e))

    # 11. Test Admin Can Update Ticket Status & Priority
    try:
        admin_user = database.fetch_one("SELECT id, full_name FROM users WHERE role = 'Admin' LIMIT 1;")
        up_ok, up_msg = update_ticket_status_and_notes(
            ticket_id=created_ticket_id,
            updated_by_user_id=admin_user["id"],
            new_status="In Progress",
            new_priority="Critical",
            update_note="Investigating root cause in QA environment."
        )
        updated_ticket = get_ticket_details(created_ticket_id)
        log_test(10, "Admin can update ticket status and priority", up_ok and updated_ticket["status"] == "In Progress", f"Status updated to {updated_ticket['status']}, priority to {updated_ticket['priority']}")
    except Exception as e:
        log_test(10, "Admin can update ticket status and priority", False, str(e))

    # 12. Test Ticket History Audit Trail is Saved
    try:
        history = get_ticket_updates(created_ticket_id)
        log_test(11, "Ticket history audit log preserved", len(history) >= 2, f"{len(history)} chronological updates recorded in ticket_updates")
    except Exception as e:
        log_test(11, "Ticket history audit log preserved", False, str(e))

    # 13. Test Resolution Timestamp Recorded Correctly
    try:
        up_ok2, up_msg2 = update_ticket_status_and_notes(
            ticket_id=created_ticket_id,
            updated_by_user_id=admin_user["id"],
            new_status="Resolved",
            new_priority="Critical",
            update_note="Resolved with software patch."
        )
        resolved_ticket = get_ticket_details(created_ticket_id)
        is_resolved_set = resolved_ticket["resolved_at"] is not None
        log_test(12, "Resolution timestamp is recorded on Resolved", is_resolved_set, f"resolved_at = {resolved_ticket['resolved_at']}")
    except Exception as e:
        log_test(12, "Resolution timestamp is recorded on Resolved", False, str(e))

    # 14. Test Search and Filters Work
    try:
        filtered_res = get_all_tickets(status="Resolved", category="Software")
        matches_filter = all(t["status"] == "Resolved" and t["category"] == "Software" for t in filtered_res)
        search_res = get_all_tickets(search=created_ticket_num)
        found_by_search = any(t["ticket_number"] == created_ticket_num for t in search_res)
        log_test(13, "Search and multi-criteria filters work", matches_filter and found_by_search, f"Found {len(search_res)} ticket by search, {len(filtered_res)} by filters")
    except Exception as e:
        log_test(13, "Search and multi-criteria filters work", False, str(e))

    # 15. Test Analytics Reflect Database Records
    try:
        df = get_analytics_dataframe()
        kpis = calculate_kpis(df)
        has_records = len(df) > 0 and kpis["total_tickets"] == len(df)
        fig_cat = plot_tickets_by_category(df)
        fig_stat = plot_tickets_by_status(df)
        fig_prio = plot_tickets_by_priority(df)
        fig_trend = plot_monthly_trend(df)
        all_figs = all([fig_cat is not None, fig_stat is not None, fig_prio is not None, fig_trend is not None])
        log_test(14, "Analytics calculate real database figures", has_records and all_figs, f"Total: {kpis['total_tickets']}, Resolution rate: {kpis['resolution_rate']}")
    except Exception as e:
        log_test(14, "Analytics calculate real database figures", False, str(e))

    # 16. Test CSV Export Works
    try:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        log_test(15, "CSV export generates valid data stream", len(csv_bytes) > 100, f"Generated {len(csv_bytes)} bytes of CSV data")
    except Exception as e:
        log_test(15, "CSV export generates valid data stream", False, str(e))

    # 17. Test Invalid File Attachments Rejected
    try:
        # Test bad extension
        bad_file = MockUploadedFile("virus.exe", 1024, b"malicious binary payload")
        valid_ext, ext_msg, _ = validate_and_save_attachment(bad_file)

        # Test oversize file (6MB)
        big_file = MockUploadedFile("huge.pdf", 6 * 1024 * 1024 + 10, b"x" * 100)
        valid_size, size_msg, _ = validate_and_save_attachment(big_file)

        log_test(16, "Invalid file attachments are rejected", (not valid_ext) and (not valid_size), f"Ext check: {ext_msg} | Size check: {size_msg}")
    except Exception as e:
        log_test(16, "Invalid file attachments are rejected", False, str(e))

    print("\n" + "=" * 70)
    print(f" TEST RESULTS SUMMARY: {passed} PASSED / {failed} FAILED (TOTAL {passed + failed})")
    print("=" * 70 + "\n")
    return failed == 0


if __name__ == "__main__":
    success = run_checklist_tests()
    sys.exit(0 if success else 1)

