"""
Storage module for managing API keys
Handles reading/writing API keys to JSON file with guild/user separation
"""

import json
import os
import logging
from typing import Optional, Dict, Any
from config import STORAGE_DIR, KEYS_FILE

logger = logging.getLogger(__name__)


def ensure_storage_dir():
    """Ensure storage directory exists"""
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
        logger.info(f"Created storage directory: {STORAGE_DIR}")


def load_api_keys() -> Dict[str, Any]:
    """
    Load all API keys from storage
    
    Returns:
        Dictionary with all stored API keys
    """
    ensure_storage_dir()
    
    if not os.path.exists(KEYS_FILE):
        logger.info("Keys file not found, creating new one")
        return {}
    
    try:
        with open(KEYS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.debug(f"Loaded {len(data)} keys from storage")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse keys.json: {e}")
        return {}
    except IOError as e:
        logger.error(f"Failed to read keys.json: {e}")
        return {}


def save_api_keys(data: Dict[str, Any]):
    """
    Save API keys to storage
    
    Args:
        data: Dictionary with API keys to save
    """
    ensure_storage_dir()
    
    try:
        # Create temp file first for safety
        temp_file = KEYS_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic replace
        os.replace(temp_file, KEYS_FILE)
        logger.debug(f"Saved {len(data)} keys to storage")
        
    except IOError as e:
        logger.error(f"Failed to save keys.json: {e}")
        raise


def get_api_key(guild_id: int, user_id: Optional[int] = None) -> Optional[str]:
    """
    Get API key for guild or user
    
    Priority: user key > guild key
    
    Args:
        guild_id: Discord guild ID
        user_id: Discord user ID (optional, for personal keys)
        
    Returns:
        API key if found, None otherwise
    """
    data = load_api_keys()
    
    # Check user key first (higher priority)
    if user_id:
        user_key = f"user_{user_id}"
        if user_key in data:
            logger.debug(f"Found user key for user {user_id}")
            return data[user_key]
    
    # Then check guild key
    guild_key = f"guild_{guild_id}"
    if guild_key in data:
        logger.debug(f"Found guild key for guild {guild_id}")
        return data[guild_key]
    
    logger.debug(f"No API key found for guild {guild_id}, user {user_id}")
    return None


def set_api_key(guild_id: int, api_key: str, user_id: Optional[int] = None):
    """
    Set API key for guild or user
    
    Args:
        guild_id: Discord guild ID
        api_key: API key to store
        user_id: Discord user ID (optional, for personal keys)
    """
    data = load_api_keys()
    
    if user_id:
        key = f"user_{user_id}"
        scope = "user"
    else:
        key = f"guild_{guild_id}"
        scope = "guild"
    
    data[key] = api_key
    save_api_keys(data)
    
    logger.info(f"Set {scope} API key for {key}")


def remove_api_key(guild_id: int, user_id: Optional[int] = None) -> bool:
    """
    Remove API key
    
    Args:
        guild_id: Discord guild ID
        user_id: Discord user ID (optional, for personal keys)
        
    Returns:
        True if key was removed, False if not found
    """
    data = load_api_keys()
    
    if user_id:
        key = f"user_{user_id}"
        scope = "user"
    else:
        key = f"guild_{guild_id}"
        scope = "guild"
    
    if key in data:
        del data[key]
        save_api_keys(data)
        logger.info(f"Removed {scope} API key for {key}")
        return True
    
    logger.debug(f"No {scope} API key found for {key}")
    return False


def has_api_key(guild_id: int, user_id: Optional[int] = None) -> bool:
    """
    Check if API key exists
    
    Args:
        guild_id: Discord guild ID
        user_id: Discord user ID (optional)
        
    Returns:
        True if key exists, False otherwise
    """
    return get_api_key(guild_id, user_id) is not None


def get_key_info(guild_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get information about API key without revealing the key itself
    
    Args:
        guild_id: Discord guild ID
        user_id: Discord user ID (optional)
        
    Returns:
        Dictionary with key information
    """
    personal_key = get_api_key(guild_id, user_id)
    guild_key = get_api_key(guild_id)
    
    return {
        "has_personal_key": personal_key is not None,
        "has_guild_key": guild_key is not None,
        "key_type": "personal" if personal_key else ("guild" if guild_key else None)
    }