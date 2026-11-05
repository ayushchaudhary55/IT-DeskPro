"""
IT DeskPro - Safe Demo Data Seeding Script
Populates fictional employees, IT support staff, realistic multi-month tickets, and audit trails.
Safe execution: checks for existing data before seeding.
"""
import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path so modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database
from utils.authentication import hash_password
import config

# Standard Demo Password for all accounts
DEMO_PASSWORD = "Password123!"

# Fictional IT Staff & Admins (2-3 accounts)
IT_STAFF = [
    {"name": "Alex Rivera", "email": "alex.rivera@deskpro.local", "role": "Admin"},
    {"name": "Sarah Chen", "email": "sarah.chen@deskpro.local", "role": "IT Support"},
    {"name": "Marcus Vance", "email": "marcus.vance@deskpro.local", "role": "IT Support"},
]

# Fictional Employees (10-15 accounts)
EMPLOYEES = [
    {"name": "Emily Watson", "email": "emily.watson@deskpro.local", "role": "Employee"},
    {"name": "David Kim", "email": "david.kim@deskpro.local", "role": "Employee"},
    {"name": "Jessica Taylor", "email": "jessica.taylor@deskpro.local", "role": "Employee"},
    {"name": "Michael Brown", "email": "michael.brown@deskpro.local", "role": "Employee"},
    {"name": "Sophia Martinez", "email": "sophia.martinez@deskpro.local", "role": "Employee"},
    {"name": "James Wilson", "email": "james.wilson@deskpro.local", "role": "Employee"},
    {"name": "Olivia Davis", "email": "olivia.davis@deskpro.local", "role": "Employee"},
    {"name": "Daniel Anderson", "email": "daniel.anderson@deskpro.local", "role": "Employee"},
    {"name": "Emma Thomas", "email": "emma.thomas@deskpro.local", "role": "Employee"},
    {"name": "Lucas Jackson", "email": "lucas.jackson@deskpro.local", "role": "Employee"},
    {"name": "Ava White", "email": "ava.white@deskpro.local", "role": "Employee"},
    {"name": "Noah Harris", "email": "noah.harris@deskpro.local", "role": "Employee"},
]

# Realistic IT Issue Templates
TICKET_TEMPLATES = [
    # Hardware
    {"title": "Laptop battery drains in under 45 minutes", "cat": "Hardware", "desc": "Dell Latitude 5420 battery health degraded suddenly after the latest Windows firmware update. Laptop dies quickly when unplugged.", "prio": "Medium"},
    {"title": "Dual monitor second display flashing black intermittently", "cat": "Hardware", "desc": "The secondary Dell 27-inch 4K monitor keeps blinking black every few minutes while connected through Thunderbolt dock.", "prio": "Medium"},
    {"title": "Docking station USB-C port physical pin loose", "cat": "Hardware", "desc": "The primary USB-C uplink cable on my CalDigit workstation dock is loose and disconnects keyboard and mouse when moved.", "prio": "High"},
    {"title": "Mechanical keyboard spacebar and enter key sticking", "cat": "Hardware", "desc": "Spilled a few drops of water on the external mechanical keyboard yesterday; keys are unresponsive and sticking.", "prio": "Low"},
    {"title": "Executive laptop dropped - cracked screen assembly", "cat": "Hardware", "desc": "Laptop slipped from bag while traveling. The top LCD lid is cracked and display is completely unreadable. Critical replacement needed.", "prio": "Critical"},
    {"title": "Desk phone display completely unpowered", "cat": "Hardware", "desc": "Cisco VoIP phone on workstation 402 is showing no power lights. Ethernet PoE cable verified intact.", "prio": "Low"},

    # Software
    {"title": "Microsoft Outlook crashing immediately on launch", "cat": "Software", "desc": "Outlook 365 crashes with error code 0xc0000005 right after splash screen. Cleared temp cache and safe mode also crashes.", "prio": "High"},
    {"title": "Excel 64-bit freezing when opening financial model pivot table", "cat": "Software", "desc": "Opening the Q3 consolidated balance sheet workbook causes Excel to become unresponsive and consume 100% CPU.", "prio": "Medium"},
    {"title": "Docker Desktop WSL2 engine failed to start after reboot", "cat": "Software", "desc": "Error: 'Virtual Machine Platform failed to initialize'. Engineering dev container workflow is currently blocked.", "prio": "High"},
    {"title": "Figma desktop client font synchronization failing", "cat": "Software", "desc": "Brand typography fonts installed locally in Windows Fonts are not being detected by Figma app.", "prio": "Low"},
    {"title": "Enterprise Zoom client microphone permission denied", "cat": "Software", "desc": "Windows privacy settings toggle for Zoom microphone access is disabled and locked by Group Policy.", "prio": "Medium"},
    {"title": "Slack enterprise notification sound muted globally", "cat": "Software", "desc": "Push notifications and chime sounds stopped playing despite Focus Assist being disabled in Windows 11.", "prio": "Low"},

    # Network
    {"title": "Cannot connect to Corporate Wi-Fi (Corp-Secure-WPA3)", "cat": "Network", "desc": "Device shows 'Can't connect to this network' when attempting 802.1x RADIUS authentication on Floor 3.", "prio": "High"},
    {"title": "GlobalProtect VPN authentication timed out on home broadband", "cat": "Network", "desc": "Portal connection to vpn.company.com handshake times out at 98% gateway selection.", "prio": "High"},
    {"title": "Workstation Ethernet port showing 100Mbps instead of 1Gbps", "cat": "Network", "desc": "LAN port negotiated down to 100BASE-TX. Large git clone operations taking unusually long.", "prio": "Low"},
    {"title": "Entire Floor 4 West Wing wireless AP offline", "cat": "Network", "desc": "Over 25 employees in marketing area disconnected simultaneously. Aruba AP LED light is blinking amber.", "prio": "Critical"},
    {"title": "Internal DNS unable to resolve dev-api.internal.corp", "cat": "Network", "desc": "DNS lookup returns NXDOMAIN when connected to office subnet. External domains resolve fine.", "prio": "Medium"},

    # Email
    {"title": "Suspected phishing email received targeting finance department", "cat": "Email", "desc": "Received urgent wire transfer request claiming to be from CFO with attachment invoice_september.pdf.exe.", "prio": "Critical"},
    {"title": "Shared mailbox 'support@company.com' not appearing in folder list", "cat": "Email", "desc": "Permission was granted by manager yesterday but Automapping has not populated the shared inbox yet.", "prio": "Medium"},
    {"title": "Out of Office automatic reply rule looping endlessly", "cat": "Email", "desc": "Automated bounce message is sending duplicate auto-replies to external vendors every 2 minutes.", "prio": "High"},
    {"title": "Distribution group emails rejected by Spam Filter", "cat": "Email", "desc": "Legitimate company newsletter sent to all-staff@company.com was quarantined by Defender for Office.", "prio": "Medium"},
    {"title": "Mailbox storage quota warning 95% full", "cat": "Email", "desc": "Exchange Online mailbox approaching 49.5 GB limit. Need archiving enabled or quota extension.", "prio": "Low"},

    # Access / Login
    {"title": "Active Directory domain account locked out after password reset", "cat": "Access/Login", "desc": "Reset password through portal but account immediately locked out due to cached iPhone Exchange credentials.", "prio": "High"},
    {"title": "Okta MFA push notification not delivering to new phone", "cat": "Access/Login", "desc": "Upgraded to new iPhone and lost Okta Verify token generator. Need MFA device registration reset.", "prio": "High"},
    {"title": "GitHub Enterprise organization SSO authorization failed", "cat": "Access/Login", "desc": "Attempting to access private company repositories prompts 'SSO token has expired or not authorized'.", "prio": "Medium"},
    {"title": "ERP SAP production login credentials requested for new hire", "cat": "Access/Login", "desc": "Finance analyst requires read-only transaction access to SAP modules FI and CO approved by VP.", "prio": "Medium"},
    {"title": "Root AWS Console session access alert during off-hours", "cat": "Access/Login", "desc": "CloudTrail triggered high-severity alert for root user login without MFA from unknown IP address.", "prio": "Critical"},

    # Other
    {"title": "Office badge reader not recognizing RFID chip at North gate", "cat": "Other", "desc": "Turnstile reader beeps red when tapping employee security badge. Facilities requested IT re-encode chip.", "prio": "Low"},
    {"title": "Conference room Zoom Rooms touchscreen controller frozen", "cat": "Other", "desc": "Boardroom Polycom touch panel is stuck on reboot screen before scheduled executive meeting.", "prio": "High"},
    {"title": "Heavy printer paper jam in Finance Department Canon Copier", "cat": "Other", "desc": "Paper stuck in internal duplex feeder tray 2 with error code E000020-0001.", "prio": "Medium"},
    {"title": "Ergonomic standing desk motor control box clicking and non-responsive", "cat": "Other", "desc": "Desk height adjustment keypad showing error code E08. Resetting power cable did not resolve.", "prio": "Low"},
]

RESOLUTION_NOTES = [
    "Identified corrupt profile registry entries. Cleared application cache and rebuilt mailbox profile. Issue verified resolved by user.",
    "Replaced faulty USB-C cable and updated Thunderbolt dock firmware to latest vendor release. Display is stable now.",
    "Reset Active Directory lock count and flushed stale Kerberos tickets. Employee verified successful login.",
    "Upgraded device driver to latest manufacturer package. Hardware self-test diagnostics passed with zero errors.",
    "Swapped network patch cable at patch panel port 24 and rebooted PoE switch port. Gigabit link speed restored.",
    "Quarantined malicious sender domain at perimeter firewall and initiated endpoint scan on affected machine. No malware traces found.",
    "Provisioned requested role-based security group access in Azure AD following managerial sign-off.",
    "Deployed emergency replacement laptop pre-loaded with standard corporate image. User data restored from OneDrive backup."
]


def seed_database(force: bool = False):
    """Inserts demo accounts and multi-month tickets safely."""
    print("=" * 60)
    print(" IT DeskPro — Demo Data Seeder")
    print("=" * 60)

    # 1. Initialize schema if not present
    database.init_database_if_needed()

    # 2. Check if users or tickets already exist
    existing_users = database.fetch_all("SELECT id, email, role FROM users;")
    existing_tickets = database.fetch_all("SELECT id FROM tickets;")

    if len(existing_users) > 0 and not force:
        print(f"\n⚠️  Found {len(existing_users)} existing users and {len(existing_tickets)} tickets.")
        print("To safely preserve existing data, seeding was skipped.")
        print("Run with '--force' flag if you explicitly want to re-seed demo data.\n")
        return

    if force:
        print("⚡ Force flag provided. Clearing old demo data...")
        database.execute_query("DELETE FROM ticket_updates;", commit=True)
        database.execute_query("DELETE FROM tickets;", commit=True)
        database.execute_query("DELETE FROM users;", commit=True)

    print("\n[1/3] Creating IT Staff and Admin accounts...")
    hashed_pwd = hash_password(DEMO_PASSWORD)

    it_user_ids = []
    for staff in IT_STAFF:
        uid = database.execute_query(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s);",
            (staff["name"], staff["email"], hashed_pwd, staff["role"]),
            commit=True
        )
        it_user_ids.append((uid, staff["name"], staff["role"]))
        print(f"  ✓ Created {staff['role']}: {staff['name']} ({staff['email']})")

    print("\n[2/3] Creating Employee accounts...")
    employee_ids = []
    for emp in EMPLOYEES:
        uid = database.execute_query(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s);",
            (emp["name"], emp["email"], hashed_pwd, emp["role"]),
            commit=True
        )
        employee_ids.append((uid, emp["name"]))
        print(f"  ✓ Created Employee: {emp['name']} ({emp['email']})")

    print("\n[3/3] Generating 38 realistic tickets across the past 5 months...")
    base_year = datetime.now().year
    ticket_seq = 1

    # Date spread across the past 150 days
    now = datetime.now()

    # Create 38 tickets using combinations of templates
    for i, t_info in enumerate(TICKET_TEMPLATES + TICKET_TEMPLATES[:12]):
        emp_id, emp_name = random.choice(employee_ids)
        ticket_num = f"ITD-{base_year}-{ticket_seq:04d}"
        ticket_seq += 1

        # Spread timestamps realistically over past 150 days
        days_ago = random.randint(1, 140)
        created_time = now - timedelta(days=days_ago, hours=random.randint(1, 12), minutes=random.randint(1, 50))

        # Status distribution: roughly 45% Resolved, 20% Closed, 20% In Progress, 15% Open
        status_roll = random.random()
        if status_roll < 0.45:
            status = "Resolved"
            # Resolution took between 2 hours and 36 hours after creation
            res_hours = random.randint(2, 36)
            resolved_time = created_time + timedelta(hours=res_hours, minutes=random.randint(5, 55))
            updated_time = resolved_time
        elif status_roll < 0.65:
            status = "Closed"
            res_hours = random.randint(1, 24)
            resolved_time = created_time + timedelta(hours=res_hours)
            updated_time = resolved_time + timedelta(days=random.randint(1, 3))
        elif status_roll < 0.85:
            status = "In Progress"
            resolved_time = None
            updated_time = created_time + timedelta(hours=random.randint(2, 12))
        else:
            status = "Open"
            resolved_time = None
            updated_time = created_time

        # Insert Ticket
        tid = database.execute_query(
            """
            INSERT INTO tickets 
            (ticket_number, user_id, title, description, category, priority, status, created_at, updated_at, resolved_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (ticket_num, emp_id, t_info["title"], t_info["desc"], t_info["cat"], t_info["prio"], status, created_time, updated_time, resolved_time),
            commit=True
        )

        # Insert Initial Creation Audit Log
        database.execute_query(
            """
            INSERT INTO ticket_updates 
            (ticket_id, updated_by, previous_status, new_status, update_note, created_at)
            VALUES (%s, %s, NULL, 'Open', 'Support request logged by employee.', %s);
            """,
            (tid, emp_id, created_time),
            commit=True
        )

        # If status moved forward, add corresponding IT Support audit entry
        if status in ["In Progress", "Resolved", "Closed"]:
            it_engineer = random.choice(it_user_ids)
            progress_time = created_time + timedelta(minutes=random.randint(15, 60))
            database.execute_query(
                """
                INSERT INTO ticket_updates 
                (ticket_id, updated_by, previous_status, new_status, update_note, created_at)
                VALUES (%s, %s, 'Open', 'In Progress', 'Assigned to IT engineer for diagnostic evaluation.', %s);
                """,
                (tid, it_engineer[0], progress_time),
                commit=True
            )

        if status in ["Resolved", "Closed"]:
            it_engineer = random.choice(it_user_ids)
            note = random.choice(RESOLUTION_NOTES)
            database.execute_query(
                """
                INSERT INTO ticket_updates 
                (ticket_id, updated_by, previous_status, new_status, update_note, created_at)
                VALUES (%s, %s, 'In Progress', %s, %s, %s);
                """,
                (tid, it_engineer[0], status, note, resolved_time),
                commit=True
            )

    print(f"\n🎉 Successfully seeded {len(IT_STAFF)} IT Staff accounts, {len(EMPLOYEES)} Employees, and {ticket_seq - 1} Tickets!")
    print("\nDemo Credentials (Password for all accounts is: Password123!)")
    print("-----------------------------------------------------------------")
    print("  • Admin Account:      alex.rivera@deskpro.local")
    print("  • IT Support Account: sarah.chen@deskpro.local")
    print("  • Employee Account:   emily.watson@deskpro.local")
    print("-----------------------------------------------------------------\n")


if __name__ == "__main__":
    force_run = "--force" in sys.argv
    seed_database(force=force_run)

