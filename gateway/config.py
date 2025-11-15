"""
Centralized Gateway configuration.
"""

from pathlib import Path
from typing import Optional

# Project base directory
BASE_DIR = Path(__file__).parent.parent

# Fixture paths
FIXTURES_DIR = BASE_DIR / "fixtures"
KEYS_DIR = FIXTURES_DIR / "keys"
STATUS_DIR = FIXTURES_DIR / "status"
REQUESTS_DIR = FIXTURES_DIR / "requests"

# JWKS paths
JWKS_BANK = str(FIXTURES_DIR / "jwks_issuer_bank.json")
JWKS_VERIFIER = str(FIXTURES_DIR / "jwks_verifier.json")

# Server configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8443

# Anchor configuration
ANCHOR_STORAGE_PATH = BASE_DIR / "fixtures" / "anchors" / "blockchain_anchors.json"
ANCHOR_ENABLED = True  # Set to False to disable anchoring entirely

def get_anchor_storage_path() -> Path:
    """Returns the anchor storage path."""
    return ANCHOR_STORAGE_PATH

def is_anchor_enabled() -> bool:
    """Returns whether anchoring is enabled."""
    return ANCHOR_ENABLED

def get_fixtures_dir() -> Path:
    """Returns the fixtures directory."""
    return FIXTURES_DIR

def get_keys_dir() -> Path:
    """Returns the keys directory."""
    return KEYS_DIR

def get_status_dir() -> Path:
    """Returns the status directory."""
    return STATUS_DIR
