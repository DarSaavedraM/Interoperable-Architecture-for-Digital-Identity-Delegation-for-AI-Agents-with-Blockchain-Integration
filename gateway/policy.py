"""
Policy loading and management for verification.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PolicyError(Exception):
    """Exception for policy-related errors."""
    pass


def load_policy(policy_id: str) -> Dict[str, Any]:
    """
    Loads a verification policy from the filesystem.
    
    Args:
        policy_id: Policy ID (e.g., "P-001")
        
    Returns:
        Dict with policy content
        
    Raises:
        PolicyError: If policy is not found or cannot be loaded
    """
    try:
        base_dir = Path(__file__).parent.parent.resolve()
    except Exception:
        # Fallback: use current directory
        base_dir = Path.cwd()
    
    # Normalize policy_id: "P-001" -> "P001"
    normalized_id = policy_id.replace("-", "")
    fixtures_dir = base_dir / "fixtures"
    
    # Find policy file (case-insensitive for Windows)
    policy_file = None
    if fixtures_dir.exists():
        policy_files = list(fixtures_dir.glob("policy_*.json"))
        for pf in policy_files:
            pf_normalized = pf.stem.replace("policy_", "").upper()
            if pf_normalized == normalized_id.upper():
                policy_file = pf
                break
    
    # If not found, try direct construction
    if policy_file is None:
        policy_file = fixtures_dir / f"policy_{normalized_id}.json"
    
    logger.debug(f"Loading policy: id={policy_id}, normalized={normalized_id}, path={policy_file}")
    
    if not policy_file.exists():
        available = [f.name for f in fixtures_dir.glob("policy_*.json")] if fixtures_dir.exists() else []
        raise PolicyError(
            f"Policy '{policy_id}' not found. "
            f"Looked for: {policy_file.absolute()}, "
            f"Available: {available}"
        )
    
    try:
        return json.loads(policy_file.read_text())
    except (json.JSONDecodeError, IOError) as e:
        raise PolicyError(f"Error loading policy from {policy_file}: {str(e)}")
