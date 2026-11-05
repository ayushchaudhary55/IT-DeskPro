"""
IT DeskPro - Application Configuration
Handles environment variables, constants, categories, priorities, and styling colors.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "it_deskpro")

# App Configuration
APP_NAME = os.getenv("APP_NAME", "IT DeskPro")
APP_TAGLINE = "Enterprise IT Service Desk & Ticket Analytics"

# Uploads Configuration
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
ALLOWED_EXTENSIONS = [
    ext.strip().lower()
    for ext in os.getenv("ALLOWED_EXTENSIONS", "png,jpg,jpeg,pdf,txt,docx,xlsx,log").split(",")
]

# Business Logic Choices
ROLES = ["Employee", "IT Support", "Admin"]

CATEGORIES = [
    "Hardware",
    "Software",
    "Network",
    "Email",
    "Access/Login",
    "Other",
]

PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

STATUSES = [
    "Open",
    "In Progress",
    "Resolved",
    "Closed",
]

# SaaS Color Palette for Badges & Charts
STATUS_COLORS = {
    "Open": "#2563EB",         # Royal Blue
    "In Progress": "#D97706",  # Amber / Warm Orange
    "Resolved": "#10B981",     # Emerald Green
    "Closed": "#64748B",       # Slate Gray
}

PRIORITY_COLORS = {
    "Low": "#10B981",          # Emerald
    "Medium": "#3B82F6",       # Blue
    "High": "#F59E0B",         # Amber
    "Critical": "#EF4444",     # Crimson Red
}

CATEGORY_ICONS = {
    "Hardware": "🖥️",
    "Software": "💾",
    "Network": "🌐",
    "Email": "✉️",
    "Access/Login": "🔑",
    "Other": "📌",
}

