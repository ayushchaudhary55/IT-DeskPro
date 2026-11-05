"""
IT DeskPro - Input Validation and Security Helpers
Validates emails, passwords, input forms, and file uploads.
"""
import os
import re
import uuid
from pathlib import Path
import config

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: str) -> tuple[bool, str]:
    """Validates email format."""
    if not email or not isinstance(email, str):
        return False, "Email address is required."
    clean_email = email.strip().lower()
    if len(clean_email) > 100:
        return False, "Email cannot exceed 100 characters."
    if not EMAIL_REGEX.match(clean_email):
        return False, "Please enter a valid email address (e.g. name@company.com)."
    return True, clean_email


def validate_password(password: str, min_length: int = 6) -> tuple[bool, str]:
    """Validates password constraints."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long."
    return True, ""


def sanitize_input(text: str, max_length: int = 5000) -> str:
    """Sanitizes text by stripping whitespace and truncating if necessary."""
    if text is None:
        return ""
    text = str(text).strip()
    return text[:max_length]


def validate_ticket_input(title: str, description: str, category: str, priority: str) -> tuple[bool, str]:
    """Validates all required ticket submission fields."""
    clean_title = sanitize_input(title, 200)
    clean_desc = sanitize_input(description, 5000)

    if not clean_title or len(clean_title) < 5:
        return False, "Ticket title is required and must be at least 5 characters long."
    if not clean_desc or len(clean_desc) < 10:
        return False, "Detailed description is required and must be at least 10 characters long."
    if category not in config.CATEGORIES:
        return False, f"Please select a valid category from: {', '.join(config.CATEGORIES)}"
    if priority not in config.PRIORITIES:
        return False, f"Please select a valid priority from: {', '.join(config.PRIORITIES)}"

    return True, ""


def validate_and_save_attachment(uploaded_file) -> tuple[bool, str, str]:
    """
    Validates uploaded file size and extension, then safely writes it to the uploads folder.
    Returns: (is_valid: bool, file_path_or_msg: str, original_filename: str)
    """
    if uploaded_file is None:
        return True, "", ""

    filename = uploaded_file.name
    # Extract extension
    file_ext = Path(filename).suffix.lower().lstrip(".")
    if not file_ext:
        return False, "File must have a valid extension.", filename

    if file_ext not in config.ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(config.ALLOWED_EXTENSIONS)
        return False, f"Unsupported file type (.{file_ext}). Allowed formats: {allowed_list}", filename

    # Check file size (bytes to MB)
    file_size_bytes = uploaded_file.size
    max_size_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_size_bytes:
        return False, f"File exceeds maximum allowed size of {config.MAX_UPLOAD_SIZE_MB} MB.", filename

    # Secure unique filename generation
    safe_basename = re.sub(r"[^a-zA-Z0-9_\.-]", "_", Path(filename).stem)[:40]
    unique_filename = f"{uuid.uuid4().hex[:10]}_{safe_basename}.{file_ext}"
    target_path = config.UPLOAD_DIR / unique_filename

    try:
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True, str(target_path), filename
    except Exception as ex:
        return False, f"Error saving file attachment: {str(ex)}", filename

