"""
Configuration file for Majestic RP Marketplace Bot
Contains all constants, API settings, and bot configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# DISCORD CONFIGURATION
# ============================================================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN не найден в переменных окружения! Создайте .env файл.")

# ============================================================================
# MAJESTIC RP API CONFIGURATION
# ============================================================================
MAJESTIC_API_BASE_URL = "https://api.majestic-rp.com"  # Base URL for API

# ============================================================================
# CATEGORIES CONFIGURATION
# ============================================================================
CATEGORIES = {
    "vehicles": "🚗 Транспорт",
    "items": "📦 Предметы",
    "houses": "🏠 Дома",
    "apartments": "🏢 Квартиры",
    "warehouses": "📦 Склады",
    "offices": "🏢 Офисы",
    "clothes": "👕 Одежда"
}

# Reverse mapping for easy lookup
CATEGORY_NAMES = {v: k for k, v in CATEGORIES.items()}

# ============================================================================
# SERVERS CONFIGURATION
# ============================================================================
SUPPORTED_SERVERS = [1, 2, 3, 4, 5]  # List of supported server IDs
DEFAULT_SERVER = 1  # Default server if not specified

# ============================================================================
# EMBED COLORS
# ============================================================================
COLORS = {
    "success": 0x00ff00,      # Green - success messages
    "error": 0xff0000,        # Red - error messages
    "info": 0x3498db,         # Blue - info messages
    "warning": 0xffaa00,      # Orange - warnings
    "primary": 0x5865F2,      # Discord Blurple - primary actions
    "vehicles": 0x3498db,     # Blue for vehicles
    "items": 0x2ecc71,        # Green for items
    "houses": 0xe74c3c,       # Red for houses
    "apartments": 0x9b59b6,   # Purple for apartments
    "warehouses": 0xf39c12,   # Orange for warehouses
    "offices": 0x1abc9c,      # Teal for offices
    "clothes": 0xe91e63       # Pink for clothes
}

# ============================================================================
# API REQUEST SETTINGS
# ============================================================================
API_TIMEOUT = 30  # Request timeout in seconds
API_RETRY_ATTEMPTS = 3  # Number of retry attempts for failed requests

# ============================================================================
# PAGINATION SETTINGS
# ============================================================================
LISTINGS_PER_PAGE = 10  # Number of listings per page
MAX_PAGES = 10  # Maximum number of pages to prevent abuse

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# BOT SETTINGS
# ============================================================================
BOT_PREFIX = "!"  # Prefix for text commands (not used for slash commands)
BOT_STATUS = "маркетплейс Majestic RP"  # Bot status text
BOT_TYPE = discord.ActivityType.watching  # Type of bot activity

# ============================================================================
# STORAGE SETTINGS
# ============================================================================
STORAGE_DIR = "data"
KEYS_FILE = os.path.join(STORAGE_DIR, "keys.json")

# ============================================================================
# SECURITY SETTINGS
# ============================================================================
# Minimum length for API key validation
MIN_API_KEY_LENGTH = 10

# Ephemeral message timeout (for sensitive data)
EPHEMERAL_TIMEOUT = 180  # 3 minutes