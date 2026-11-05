"""
IT DeskPro - Authentication & Role Management Module
Provides secure bcrypt password hashing, session state helpers, and MySQL user operations.
"""
import bcrypt
import streamlit as st
import database
from utils.validation import validate_email, validate_password, sanitize_input


def hash_password(plain_password: str) -> str:
    """Hashes a plain text password using bcrypt with a generated salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def authenticate_user(email: str, password: str) -> tuple[bool, str, dict | None]:
    """
    Validates user credentials against MySQL.
    Returns (success: bool, message: str, user_dict: dict | None)
    """
    valid_email, clean_email_or_msg = validate_email(email)
    if not valid_email:
        return False, clean_email_or_msg, None

    if not password:
        return False, "Password cannot be empty.", None

    query = "SELECT id, full_name, email, password_hash, role, created_at FROM users WHERE email = %s LIMIT 1;"
    try:
        user = database.fetch_one(query, (clean_email_or_msg,))
        if not user:
            return False, "Invalid email or password.", None

        if not verify_password(password, user["password_hash"]):
            return False, "Invalid email or password.", None

        # Sanitize user dict for session (omit password hash)
        user_session = {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user["created_at"],
        }
        return True, "Login successful.", user_session
    except Exception as ex:
        return False, "An error occurred while connecting to the authentication server.", None


def register_user(full_name: str, email: str, password: str, role: str = "Employee") -> tuple[bool, str, int | None]:
    """
    Registers a new user into MySQL with a securely hashed password.
    Returns (success: bool, message: str, new_user_id: int | None)
    """
    clean_name = sanitize_input(full_name, 100)
    if not clean_name or len(clean_name) < 2:
        return False, "Full name must be at least 2 characters.", None

    valid_email, clean_email_or_msg = validate_email(email)
    if not valid_email:
        return False, clean_email_or_msg, None

    valid_pwd, pwd_msg = validate_password(password)
    if not valid_pwd:
        return False, pwd_msg, None

    valid_roles = ["Employee", "IT Support", "Admin"]
    if role not in valid_roles:
        return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}", None

    # Check if email is already registered
    check_query = "SELECT id FROM users WHERE email = %s LIMIT 1;"
    try:
        existing = database.fetch_one(check_query, (clean_email_or_msg,))
        if existing:
            return False, "An account with this email address already exists.", None

        pwd_hash = hash_password(password)
        insert_query = """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, %s);
        """
        user_id = database.execute_query(
            insert_query,
            (clean_name, clean_email_or_msg, pwd_hash, role),
            commit=True
        )
        return True, "User registered successfully.", user_id
    except Exception as ex:
        return False, f"Registration failed due to a database error: {str(ex)}", None


def get_user_by_id(user_id: int) -> dict | None:
    """Retrieves safe user profile by ID."""
    query = "SELECT id, full_name, email, role, created_at FROM users WHERE id = %s LIMIT 1;"
    try:
        return database.fetch_one(query, (user_id,))
    except Exception:
        return None


def update_user_profile(user_id: int, full_name: str) -> tuple[bool, str]:
    """Updates user's display name."""
    clean_name = sanitize_input(full_name, 100)
    if not clean_name or len(clean_name) < 2:
        return False, "Name must be at least 2 characters."

    query = "UPDATE users SET full_name = %s WHERE id = %s;"
    try:
        database.execute_query(query, (clean_name, user_id), commit=True)
        # Update session state if modifying current user
        if st.session_state.get("user") and st.session_state["user"]["id"] == user_id:
            st.session_state["user"]["full_name"] = clean_name
        return True, "Profile name updated successfully."
    except Exception as ex:
        return False, "Failed to update profile name."


def change_user_password(user_id: int, current_password: str, new_password: str) -> tuple[bool, str]:
    """Changes user's password after verifying existing password."""
    valid_new, new_msg = validate_password(new_password)
    if not valid_new:
        return False, new_msg

    try:
        query = "SELECT password_hash FROM users WHERE id = %s LIMIT 1;"
        user = database.fetch_one(query, (user_id,))
        if not user:
            return False, "User not found."

        if not verify_password(current_password, user["password_hash"]):
            return False, "Current password does not match."

        new_hash = hash_password(new_password)
        update_query = "UPDATE users SET password_hash = %s WHERE id = %s;"
        database.execute_query(update_query, (new_hash, user_id), commit=True)
        return True, "Password has been successfully changed."
    except Exception as ex:
        return False, "An error occurred while updating password."


# Streamlit Session State Management Helpers

def is_logged_in() -> bool:
    """Returns True if a valid user is in session state."""
    return "user" in st.session_state and st.session_state["user"] is not None


def get_current_user() -> dict | None:
    """Returns current logged-in user dictionary."""
    return st.session_state.get("user")


def login_user_session(user_dict: dict):
    """Stores user information in session state."""
    st.session_state["user"] = user_dict


def logout_user_session():
    """Clears user session state and triggers rerun."""
    st.session_state["user"] = None
    if "current_page" in st.session_state:
        st.session_state["current_page"] = "Login"
    st.rerun()


def check_role_access(allowed_roles: list[str]) -> bool:
    """
    Checks if current user has one of the allowed roles.
    If not, renders a warning and returns False.
    """
    if not is_logged_in():
        st.warning("⚠️ Please sign in to access this page.")
        return False

    current_role = st.session_state["user"].get("role")
    if current_role not in allowed_roles:
        st.error(f"⛔ Access Denied: This area requires one of the following roles: {', '.join(allowed_roles)}.")
        return False
    return True

