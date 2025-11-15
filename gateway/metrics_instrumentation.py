"""
Metrics instrumentation helpers for gateway layer.
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Add scripts directory to path for metrics_collector import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scripts.metrics_collector import get_collector
    METRICS_AVAILABLE = True
    import logging
    logger = logging.getLogger(__name__)
    logger.info("[METRICS] Metrics collector module loaded successfully")
except ImportError as e:
    METRICS_AVAILABLE = False
    get_collector = None
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"[METRICS] Failed to import metrics collector: {e}")


def get_metrics_collector():
    """Get metrics collector if available, otherwise return None."""
    if METRICS_AVAILABLE:
        collector = get_collector()
        return collector
    else:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("[METRICS] Metrics collector not available (METRICS_AVAILABLE=False)")
    return None


def record_request_size(collector, request_data: dict) -> None:
    """Record request size in bytes."""
    if collector and collector.current:
        request_size = len(json.dumps(request_data, sort_keys=True).encode('utf-8'))
        # Directly update size
        collector.current.sizes.request_size_bytes = request_size


def record_cvc_size(collector, cvc: dict) -> None:
    """Record CVC size in bytes."""
    if collector and collector.current:
        cvc_size = len(json.dumps(cvc, sort_keys=True).encode('utf-8'))
        # Directly update size
        collector.current.sizes.cvc_serialized_size_bytes = cvc_size


def record_vc_jwt_size(collector, jwt_token: str) -> None:
    """Record VC-JWT size in bytes."""
    if collector and collector.current:
        jwt_size = len(jwt_token.encode('utf-8'))
        # Directly update size
        collector.current.sizes.vc_jwt_size_bytes = jwt_size


def record_dg_chain_size(collector, delegation_chain: list) -> None:
    """Record delegation chain size in bytes."""
    if collector and collector.current:
        chain_size = sum(len(token.encode('utf-8')) for token in delegation_chain)
        # Directly update size
        collector.current.sizes.dg_chain_size_bytes = chain_size


def record_vro_size(collector, vro_jwt: str) -> None:
    """Record VRO JWT size in bytes."""
    if collector and collector.current:
        vro_size = len(vro_jwt.encode('utf-8'))
        # Directly update size
        collector.current.sizes.vro_jwt_size_bytes = vro_size

