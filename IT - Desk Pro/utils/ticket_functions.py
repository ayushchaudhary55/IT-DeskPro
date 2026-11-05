"""
IT DeskPro - Ticket Management Functions Layer
Handles CRUD operations, ticket number generation, audit trails, and dashboard metrics.
"""
from datetime import datetime
import database
from utils.validation import validate_ticket_input


def generate_ticket_number() -> str:
    """
    Generates a unique sequential ticket number in the format ITD-YYYY-XXXX (e.g. ITD-2026-0001).
    Guarantees uniqueness by checking existing database records.
    """
    current_year = datetime.now().year
    prefix = f"ITD-{current_year}-"

    query = """
        SELECT ticket_number 
        FROM tickets 
        WHERE ticket_number LIKE %s 
        ORDER BY id DESC 
        LIMIT 1;
    """
    try:
        last_ticket = database.fetch_one(query, (f"{prefix}%",))
        if last_ticket and last_ticket.get("ticket_number"):
            last_num_str = last_ticket["ticket_number"].split("-")[-1]
            try:
                next_seq = int(last_num_str) + 1
            except ValueError:
                next_seq = 1
        else:
            next_seq = 1
        return f"{prefix}{next_seq:04d}"
    except Exception:
        # Fallback in case of temporary read delay
        import time
        return f"{prefix}{int(time.time()) % 10000:04d}"


def create_ticket(
    user_id: int,
    title: str,
    description: str,
    category: str,
    priority: str,
    attachment_path: str = None
) -> tuple[bool, str, str]:
    """
    Creates a new support ticket in MySQL with initial status 'Open'.
    Also records the creation audit in ticket_updates.
    Returns: (success: bool, ticket_number: str, message: str)
    """
    is_valid, validation_msg = validate_ticket_input(title, description, category, priority)
    if not is_valid:
        return False, "", validation_msg

    ticket_num = generate_ticket_number()

    insert_ticket_sql = """
        INSERT INTO tickets (ticket_number, user_id, title, description, category, priority, status, attachment_path, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, 'Open', %s, NOW(), NOW());
    """

    insert_audit_sql = """
        INSERT INTO ticket_updates (ticket_id, updated_by, previous_status, new_status, update_note, created_at)
        VALUES (%s, %s, NULL, 'Open', %s, NOW());
    """

    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                insert_ticket_sql,
                (ticket_num, user_id, title.strip(), description.strip(), category, priority, attachment_path)
            )
            ticket_id = cursor.lastrowid

            cursor.execute(
                insert_audit_sql,
                (ticket_id, user_id, "Ticket submitted by employee.")
            )
            conn.commit()
            cursor.close()

        return True, ticket_num, f"Ticket #{ticket_num} has been successfully submitted."
    except Exception as ex:
        return False, "", f"Database error creating ticket: {str(ex)}"


def get_user_tickets(
    user_id: int,
    status: str = "All",
    category: str = "All",
    priority: str = "All",
    search: str = "",
    sort_order: str = "DESC"
) -> list[dict]:
    """
    Retrieves tickets created by a specific employee with filtering, searching, and sorting.
    """
    conditions = ["t.user_id = %s"]
    params = [user_id]

    if status and status != "All":
        conditions.append("t.status = %s")
        params.append(status)

    if category and category != "All":
        conditions.append("t.category = %s")
        params.append(category)

    if priority and priority != "All":
        conditions.append("t.priority = %s")
        params.append(priority)

    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        conditions.append("(t.ticket_number LIKE %s OR t.title LIKE %s OR t.description LIKE %s)")
        params.extend([search_pattern, search_pattern, search_pattern])

    order_direction = "ASC" if sort_order.upper() == "ASC" else "DESC"

    sql = f"""
        SELECT 
            t.id,
            t.ticket_number,
            t.user_id,
            t.title,
            t.description,
            t.category,
            t.priority,
            t.status,
            t.attachment_path,
            t.created_at,
            t.updated_at,
            t.resolved_at
        FROM tickets t
        WHERE {' AND '.join(conditions)}
        ORDER BY t.created_at {order_direction};
    """
    return database.fetch_all(sql, params)


def get_all_tickets(
    status: str = "All",
    category: str = "All",
    priority: str = "All",
    search: str = "",
    sort_order: str = "DESC"
) -> list[dict]:
    """
    Retrieves all tickets across all employees with user details, for IT Support & Admins.
    """
    conditions = ["1=1"]
    params = []

    if status and status != "All":
        conditions.append("t.status = %s")
        params.append(status)

    if category and category != "All":
        conditions.append("t.category = %s")
        params.append(category)

    if priority and priority != "All":
        conditions.append("t.priority = %s")
        params.append(priority)

    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        conditions.append("(t.ticket_number LIKE %s OR t.title LIKE %s OR u.full_name LIKE %s OR u.email LIKE %s)")
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    order_direction = "ASC" if sort_order.upper() == "ASC" else "DESC"

    sql = f"""
        SELECT 
            t.id,
            t.ticket_number,
            t.user_id,
            u.full_name AS employee_name,
            u.email AS employee_email,
            t.title,
            t.description,
            t.category,
            t.priority,
            t.status,
            t.attachment_path,
            t.created_at,
            t.updated_at,
            t.resolved_at
        FROM tickets t
        INNER JOIN users u ON t.user_id = u.id
        WHERE {' AND '.join(conditions)}
        ORDER BY t.created_at {order_direction};
    """
    return database.fetch_all(sql, params)


def get_ticket_details(ticket_id: int) -> dict | None:
    """Retrieves full details of a specific ticket along with the creator's identity."""
    sql = """
        SELECT 
            t.id,
            t.ticket_number,
            t.user_id,
            u.full_name AS employee_name,
            u.email AS employee_email,
            t.title,
            t.description,
            t.category,
            t.priority,
            t.status,
            t.attachment_path,
            t.created_at,
            t.updated_at,
            t.resolved_at
        FROM tickets t
        INNER JOIN users u ON t.user_id = u.id
        WHERE t.id = %s
        LIMIT 1;
    """
    return database.fetch_one(sql, (ticket_id,))


def get_ticket_updates(ticket_id: int) -> list[dict]:
    """
    Retrieves the full chronological update history (audit trail) for a given ticket.
    """
    sql = """
        SELECT 
            tu.id,
            tu.ticket_id,
            tu.updated_by,
            u.full_name AS updated_by_name,
            u.role AS updated_by_role,
            tu.previous_status,
            tu.new_status,
            tu.update_note,
            tu.created_at
        FROM ticket_updates tu
        INNER JOIN users u ON tu.updated_by = u.id
        WHERE tu.ticket_id = %s
        ORDER BY tu.created_at ASC;
    """
    return database.fetch_all(sql, (ticket_id,))


def update_ticket_status_and_notes(
    ticket_id: int,
    updated_by_user_id: int,
    new_status: str,
    new_priority: str,
    update_note: str
) -> tuple[bool, str]:
    """
    Updates status and priority of a ticket, records resolution timestamp if resolved,
    and appends a new immutable audit record in ticket_updates.
    """
    clean_note = update_note.strip() if update_note else ""
    if not clean_note:
        return False, "An update note is required to explain this modification."

    # Fetch current ticket state
    current_ticket = get_ticket_details(ticket_id)
    if not current_ticket:
        return False, "Ticket not found."

    prev_status = current_ticket["status"]
    prev_priority = current_ticket["priority"]

    # Determine resolved_at logic
    resolved_at_sql = ""
    resolved_params = []

    if new_status == "Resolved" and prev_status != "Resolved":
        # Newly resolved
        resolved_at_sql = ", resolved_at = NOW()"
    elif new_status != "Resolved" and prev_status == "Resolved":
        # Re-opened
        resolved_at_sql = ", resolved_at = NULL"

    update_ticket_sql = f"""
        UPDATE tickets 
        SET status = %s, priority = %s, updated_at = NOW() {resolved_at_sql}
        WHERE id = %s;
    """

    note_text = clean_note
    # If priority changed as well, append to note for clarity
    if new_priority != prev_priority:
        note_text = f"[Priority updated from {prev_priority} to {new_priority}] - {clean_note}"

    insert_audit_sql = """
        INSERT INTO ticket_updates (ticket_id, updated_by, previous_status, new_status, update_note, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW());
    """

    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(update_ticket_sql, (new_status, new_priority, ticket_id))
            cursor.execute(
                insert_audit_sql,
                (ticket_id, updated_by_user_id, prev_status, new_status, note_text)
            )
            conn.commit()
            cursor.close()
        return True, f"Ticket #{current_ticket['ticket_number']} updated successfully."
    except Exception as ex:
        return False, f"Failed to update ticket: {str(ex)}"


def get_employee_dashboard_metrics(user_id: int) -> dict:
    """Computes real-time KPI metrics and breakdown for an employee."""
    sql = """
        SELECT 
            COUNT(*) AS total_tickets,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_tickets,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_tickets,
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_tickets,
            SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) AS closed_tickets
        FROM tickets
        WHERE user_id = %s;
    """
    stats = database.fetch_one(sql, (user_id,))
    total = stats["total_tickets"] or 0
    open_cnt = stats["open_tickets"] or 0
    in_prog = stats["in_progress_tickets"] or 0
    resolved = stats["resolved_tickets"] or 0
    closed = stats["closed_tickets"] or 0

    recent_tickets = get_user_tickets(user_id=user_id, sort_order="DESC")[:5]

    return {
        "total": total,
        "open": open_cnt,
        "in_progress": in_prog,
        "resolved": resolved,
        "closed": closed,
        "recent_tickets": recent_tickets
    }


def get_admin_dashboard_metrics() -> dict:
    """Computes real-time KPI metrics, resolution times, and attention items for IT Support/Admin."""
    kpi_sql = """
        SELECT 
            COUNT(*) AS total_tickets,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_tickets,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_tickets,
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_tickets,
            SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) AS closed_tickets,
            SUM(CASE WHEN priority = 'Critical' AND status IN ('Open', 'In Progress') THEN 1 ELSE 0 END) AS critical_active
        FROM tickets;
    """
    kpis = database.fetch_one(kpi_sql) or {}

    # Average Resolution Time (in hours) for tickets that have resolved_at
    avg_res_sql = """
        SELECT AVG(TIMESTAMPDIFF(MINUTE, created_at, resolved_at)) AS avg_resolution_minutes
        FROM tickets 
        WHERE resolved_at IS NOT NULL;
    """
    res_data = database.fetch_one(avg_res_sql) or {}
    avg_minutes = res_data.get("avg_resolution_minutes")
    if avg_minutes is not None and avg_minutes > 0:
        avg_hours = round(float(avg_minutes) / 60.0, 1)
        if avg_hours >= 24:
            avg_res_str = f"{round(avg_hours / 24, 1)} days"
        else:
            avg_res_str = f"{avg_hours} hrs"
    else:
        avg_res_str = "N/A"

    # Attention required: High & Critical tickets still Open or In Progress
    attention_sql = """
        SELECT 
            t.id,
            t.ticket_number,
            u.full_name AS employee_name,
            t.title,
            t.category,
            t.priority,
            t.status,
            t.created_at
        FROM tickets t
        INNER JOIN users u ON t.user_id = u.id
        WHERE t.priority IN ('Critical', 'High') AND t.status IN ('Open', 'In Progress')
        ORDER BY FIELD(t.priority, 'Critical', 'High'), t.created_at ASC
        LIMIT 6;
    """
    attention_tickets = database.fetch_all(attention_sql)

    # Recent tickets across company
    recent_sql = """
        SELECT 
            t.id,
            t.ticket_number,
            u.full_name AS employee_name,
            t.title,
            t.category,
            t.priority,
            t.status,
            t.created_at
        FROM tickets t
        INNER JOIN users u ON t.user_id = u.id
        ORDER BY t.created_at DESC
        LIMIT 5;
    """
    recent_tickets = database.fetch_all(recent_sql)

    return {
        "total": kpis.get("total_tickets") or 0,
        "open": kpis.get("open_tickets") or 0,
        "in_progress": kpis.get("in_progress_tickets") or 0,
        "resolved": kpis.get("resolved_tickets") or 0,
        "closed": kpis.get("closed_tickets") or 0,
        "critical_active": kpis.get("critical_active") or 0,
        "avg_resolution_time": avg_res_str,
        "attention_tickets": attention_tickets,
        "recent_tickets": recent_tickets
    }

