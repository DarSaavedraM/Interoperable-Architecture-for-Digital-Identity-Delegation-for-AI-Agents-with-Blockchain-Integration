"""
Metrics collection framework for research evaluation.
"""

import time
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class TimingMetrics:
    """Timing metrics for a single operation."""
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    
    def start(self) -> None:
        """Start timing."""
        self.start_time = time.perf_counter()
    
    def stop(self) -> None:
        """Stop timing and calculate duration."""
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class SizeMetrics:
    """Size metrics for tokens and structures."""
    vc_jwt_size_bytes: int = 0
    dg_chain_size_bytes: int = 0
    vro_jwt_size_bytes: int = 0
    cvc_serialized_size_bytes: int = 0
    request_size_bytes: int = 0


@dataclass
class InvariantMetrics:
    """Invariant verification metrics."""
    scope_containment_passed: bool = False
    temporal_validity_passed: bool = False
    signature_verification_passed: bool = False
    chain_integrity_passed: bool = False
    structural_validity_passed: bool = False
    fail_closed_operation: bool = False


@dataclass
class VerificationMetrics:
    """Complete metrics for a single verification request."""
    request_id: str = ""
    scenario: str = ""
    profile: str = ""
    chain_depth: int = 0
    
    # Timing
    e2e_latency: TimingMetrics = field(default_factory=TimingMetrics)
    normalization_latency: TimingMetrics = field(default_factory=TimingMetrics)
    verification_latency: TimingMetrics = field(default_factory=TimingMetrics)
    vro_signing_latency: TimingMetrics = field(default_factory=TimingMetrics)
    status_fetch_latency: TimingMetrics = field(default_factory=TimingMetrics)
    
    # Sizes
    sizes: SizeMetrics = field(default_factory=SizeMetrics)
    
    # Invariants
    invariants: InvariantMetrics = field(default_factory=InvariantMetrics)
    
    # Results
    success: bool = False
    error_code: Optional[str] = None
    vro_hash: Optional[str] = None
    chain_fingerprint: Optional[str] = None
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MetricsCollector:
    """Collects and aggregates metrics for research evaluation."""
    
    def __init__(self):
        self.metrics: List[VerificationMetrics] = []
        self.current: Optional[VerificationMetrics] = None
    
    def start_request(self, request_id: str, scenario: str, profile: str) -> None:
        """Start collecting metrics for a new request."""
        self.current = VerificationMetrics(
            request_id=request_id,
            scenario=scenario,
            profile=profile
        )
        self.current.e2e_latency.start()
    
    def record_normalization_start(self) -> None:
        """Record normalization start."""
        if self.current:
            self.current.normalization_latency.start()
    
    def record_normalization_end(self) -> None:
        """Record normalization end."""
        if self.current:
            self.current.normalization_latency.stop()
    
    def record_verification_start(self) -> None:
        """Record verification start."""
        if self.current:
            self.current.verification_latency.start()
    
    def record_verification_end(self) -> None:
        """Record verification end."""
        if self.current:
            self.current.verification_latency.stop()
    
    def record_vro_signing_start(self) -> None:
        """Record VRO signing start."""
        if self.current:
            self.current.vro_signing_latency.start()
    
    def record_vro_signing_end(self) -> None:
        """Record VRO signing end."""
        if self.current:
            self.current.vro_signing_latency.stop()
    
    def record_status_fetch(self, duration_ms: float) -> None:
        """Record status fetch duration."""
        if self.current:
            self.current.status_fetch_latency.duration_ms = duration_ms
    
    def record_sizes(
        self,
        vc_jwt_size: int = 0,
        dg_chain_size: int = 0,
        vro_jwt_size: int = 0,
        cvc_size: int = 0,
        request_size: int = 0
    ) -> None:
        """Record size metrics."""
        if self.current:
            self.current.sizes.vc_jwt_size_bytes = vc_jwt_size
            self.current.sizes.dg_chain_size_bytes = dg_chain_size
            self.current.sizes.vro_jwt_size_bytes = vro_jwt_size
            self.current.sizes.cvc_serialized_size_bytes = cvc_size
            self.current.sizes.request_size_bytes = request_size
    
    def record_chain_depth(self, depth: int) -> None:
        """Record delegation chain depth."""
        if self.current:
            self.current.chain_depth = depth
    
    def record_invariants(
        self,
        scope_containment: bool = False,
        temporal_validity: bool = False,
        signature_verification: bool = False,
        chain_integrity: bool = False,
        structural_validity: bool = False,
        fail_closed: bool = False
    ) -> None:
        """Record invariant verification results."""
        if self.current:
            self.current.invariants.scope_containment_passed = scope_containment
            self.current.invariants.temporal_validity_passed = temporal_validity
            self.current.invariants.signature_verification_passed = signature_verification
            self.current.invariants.chain_integrity_passed = chain_integrity
            self.current.invariants.structural_validity_passed = structural_validity
            self.current.invariants.fail_closed_operation = fail_closed
    
    def record_result(
        self,
        success: bool,
        error_code: Optional[str] = None,
        vro_hash: Optional[str] = None,
        chain_fingerprint: Optional[str] = None
    ) -> None:
        """Record verification result."""
        if self.current:
            self.current.success = success
            self.current.error_code = error_code
            self.current.vro_hash = vro_hash
            self.current.chain_fingerprint = chain_fingerprint
    
    def end_request(self) -> VerificationMetrics:
        """End request and return metrics."""
        if self.current:
            self.current.e2e_latency.stop()
            metrics = self.current
            self.metrics.append(metrics)
            self.current = None
            return metrics
        raise ValueError("No active request")
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """Get all collected metrics as dictionaries."""
        return [asdict(m) for m in self.metrics]
    
    def save_json(self, filepath: Path) -> None:
        """Save metrics to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.get_metrics(), f, indent=2)
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate aggregate statistics."""
        if not self.metrics:
            return {}
        
        stats = {
            "total_requests": len(self.metrics),
            "success_rate": sum(1 for m in self.metrics if m.success) / len(self.metrics),
            "e2e_latency": self._calculate_latency_stats([m.e2e_latency.duration_ms for m in self.metrics]),
            "normalization_latency": self._calculate_latency_stats([m.normalization_latency.duration_ms for m in self.metrics]),
            "verification_latency": self._calculate_latency_stats([m.verification_latency.duration_ms for m in self.metrics]),
            "chain_depth_distribution": self._calculate_depth_distribution(),
            "invariant_pass_rates": self._calculate_invariant_rates(),
            "size_statistics": self._calculate_size_stats(),
        }
        
        return stats
    
    def _calculate_latency_stats(self, latencies: List[float]) -> Dict[str, float]:
        """Calculate latency statistics."""
        if not latencies:
            return {}
        
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        return {
            "mean": sum(latencies) / n,
            "median": sorted_latencies[n // 2],
            "p95": sorted_latencies[int(n * 0.95)] if n > 0 else 0,
            "p99": sorted_latencies[int(n * 0.99)] if n > 0 else 0,
            "min": min(latencies),
            "max": max(latencies)
        }
    
    def _calculate_depth_distribution(self) -> Dict[int, int]:
        """Calculate chain depth distribution."""
        distribution = defaultdict(int)
        for m in self.metrics:
            distribution[m.chain_depth] += 1
        return dict(distribution)
    
    def _calculate_invariant_rates(self) -> Dict[str, float]:
        """Calculate invariant pass rates."""
        total = len(self.metrics)
        if total == 0:
            return {}
        
        return {
            "scope_containment": sum(1 for m in self.metrics if m.invariants.scope_containment_passed) / total,
            "temporal_validity": sum(1 for m in self.metrics if m.invariants.temporal_validity_passed) / total,
            "signature_verification": sum(1 for m in self.metrics if m.invariants.signature_verification_passed) / total,
            "chain_integrity": sum(1 for m in self.metrics if m.invariants.chain_integrity_passed) / total,
            "structural_validity": sum(1 for m in self.metrics if m.invariants.structural_validity_passed) / total,
        }
    
    def _calculate_size_stats(self) -> Dict[str, Dict[str, float]]:
        """Calculate size statistics."""
        vc_sizes = [m.sizes.vc_jwt_size_bytes for m in self.metrics if m.sizes.vc_jwt_size_bytes > 0]
        dg_sizes = [m.sizes.dg_chain_size_bytes for m in self.metrics if m.sizes.dg_chain_size_bytes > 0]
        vro_sizes = [m.sizes.vro_jwt_size_bytes for m in self.metrics if m.sizes.vro_jwt_size_bytes > 0]
        
        stats = {}
        if vc_sizes:
            stats["vc_jwt"] = {"mean": sum(vc_sizes) / len(vc_sizes), "max": max(vc_sizes)}
        if dg_sizes:
            stats["dg_chain"] = {"mean": sum(dg_sizes) / len(dg_sizes), "max": max(dg_sizes)}
        if vro_sizes:
            stats["vro_jwt"] = {"mean": sum(vro_sizes) / len(vro_sizes), "max": max(vro_sizes)}
        
        return stats


# Global collector instance
_collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _collector


def hash_vro(vro_jwt: str) -> str:
    """Calculate hash of VRO for determinism verification."""
    return hashlib.sha256(vro_jwt.encode()).hexdigest()[:16]


