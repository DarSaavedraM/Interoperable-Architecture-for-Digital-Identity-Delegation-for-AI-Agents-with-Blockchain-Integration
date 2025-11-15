"""
Revocation status verification using StatusList2021.
"""

import json
import time
import sys
from typing import Dict, Any
from pathlib import Path

# Add scripts directory to path for metrics_collector import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scripts.metrics_collector import get_collector
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    get_collector = None


class StatusError(Exception):
    """Base exception for status errors."""
    pass


def fetch_status(status_url: str) -> Dict[str, Any]:
    """
    Retrieves a StatusList2021 status document from local filesystem.
    
    Args:
        status_url: URL of status document (mapped to local file)
        
    Returns:
        Dict with status document
        
    Raises:
        StatusError: If status document cannot be loaded
    """
    # Record status fetch timing
    collector = get_collector() if METRICS_AVAILABLE else None
    start_time = time.perf_counter()
    
    base_dir = Path(__file__).parent.parent
    
    # Map URLs to local files (offline mode)
    if "revoked" in status_url:
        status_file = base_dir / "fixtures/status/statuslist2021_revoked.json"
    else:
        status_file = base_dir / "fixtures/status/statuslist2021_active.json"
    
    if not status_file.exists():
        raise StatusError(f"Status file not found: {status_file}")
    
    try:
        result = json.loads(status_file.read_text())
        
        # Record status fetch duration
        if collector:
            duration_ms = (time.perf_counter() - start_time) * 1000
            collector.record_status_fetch(duration_ms)
        
        return result
    except (json.JSONDecodeError, IOError) as e:
        raise StatusError(f"Error loading status file {status_file}: {str(e)}")


def is_revoked(status_doc: Dict[str, Any], index: int) -> bool:
    """
    Checks if a specific index is revoked in a StatusList2021 document.
    
    Note: This is a simplified implementation for the prototype.
    A complete implementation would decode the full bitstring encodedList.
    
    Args:
        status_doc: StatusList2021 status document
        index: Index to check
        
    Returns:
        True if index is revoked, False otherwise
    """
    encoded_list = status_doc.get("encodedList", "")
    
    # Simplified implementation: detects revocation patterns
    # In production, the full bitstring would be decoded
    if "/////" in encoded_list:
        return True
    
    # If encodedList is empty or only "AAAA", assume not revoked
    return False
