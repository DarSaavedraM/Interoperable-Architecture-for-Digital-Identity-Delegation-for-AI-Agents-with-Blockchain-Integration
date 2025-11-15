"""
Run metrics collection on batch of generated requests with blockchain anchor support.

This script processes all batch requests and collects comprehensive metrics
including blockchain anchor metrics for statistical analysis.
"""

import json
import sys
import time
import requests
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import metrics collector
from metrics_collector import (
    get_collector, hash_vro, VerificationMetrics, 
    TimingMetrics, SizeMetrics, InvariantMetrics
)

BASE_URL = "http://localhost:8443"
TIMEOUT = 30


def load_batch_metadata(requests_dir: Path) -> Dict[str, Any]:
    """Load batch metadata."""
    metadata_file = requests_dir / "batch_metadata.json"
    if not metadata_file.exists():
        raise FileNotFoundError(f"Batch metadata not found: {metadata_file}")
    
    with open(metadata_file, "r", encoding="utf-8") as f:
        return json.load(f)


def test_request_with_metrics(
    request_file: Path,
    request_meta: Dict[str, Any],
    collector
) -> Dict[str, Any]:
    """Test a single request and collect metrics."""
    if not request_file.exists():
        return {"success": False, "error": "File not found"}
    
    request_id = request_meta.get("request_id", "unknown")
    scenario = f"BATCH-{request_meta.get('profile', 'UNKNOWN')}"
    profile = request_meta.get("profile", "VC-JWT")
    chain_depth = request_meta.get("chain_depth", 0)
    require_anchor = request_meta.get("require_anchor")
    
    try:
        with open(request_file, "r", encoding="utf-8") as f:
            request_data = json.load(f)
        
        # Record request size (client-side)
        request_size = len(json.dumps(request_data, sort_keys=True).encode('utf-8'))
        
        # Make request (server will return metrics in response)
        response = requests.post(
            f"{BASE_URL}/verify",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        # Extract metrics from response
        server_metrics = None
        response_data = None
        if response.status_code == 200:
            try:
                response_data = response.json()
                server_metrics = response_data.get("metrics")
            except:
                pass
        elif response.status_code == 400:
            # Error response might also contain metrics
            try:
                error_data = response.json()
                # Metrics can be at top level or in detail dict
                if "metrics" in error_data:
                    server_metrics = error_data.get("metrics")
                elif isinstance(error_data.get("detail"), dict) and "metrics" in error_data["detail"]:
                    server_metrics = error_data["detail"].get("metrics")
                response_data = error_data
            except:
                pass
        
        # Copy metrics from response if available
        try:
            if server_metrics:
                # Safely get e2e_latency with defaults
                e2e_latency = server_metrics.get("e2e_latency", {})
                e2e_end = e2e_latency.get("end_time", 0) if isinstance(e2e_latency, dict) else 0
                e2e_duration = e2e_latency.get("duration_ms", 0) if isinstance(e2e_latency, dict) else 0
                
                # Copy metrics if server has completed processing (end_time > 0 or duration > 0)
                if e2e_end > 0 or e2e_duration > 0:
                    try:
                        # Helper to safely extract timing metrics
                        def get_timing(metrics_dict, key, default=0.0):
                            timing = metrics_dict.get(key, {})
                            if not isinstance(timing, dict):
                                return {"start_time": default, "end_time": default, "duration_ms": default}
                            return {
                                "start_time": timing.get("start_time", default),
                                "end_time": timing.get("end_time", default),
                                "duration_ms": timing.get("duration_ms", default)
                            }
                        
                        # Helper to safely extract sizes
                        def get_sizes(metrics_dict, default=0):
                            sizes = metrics_dict.get("sizes", {})
                            if not isinstance(sizes, dict):
                                return {k: default for k in ["vc_jwt_size_bytes", "dg_chain_size_bytes", "vro_jwt_size_bytes", "cvc_serialized_size_bytes"]}
                            return {
                                "vc_jwt_size_bytes": sizes.get("vc_jwt_size_bytes", default),
                                "dg_chain_size_bytes": sizes.get("dg_chain_size_bytes", default),
                                "vro_jwt_size_bytes": sizes.get("vro_jwt_size_bytes", default),
                                "cvc_serialized_size_bytes": sizes.get("cvc_serialized_size_bytes", default)
                            }
                        
                        # Helper to safely extract invariants
                        def get_invariants(metrics_dict, default=False):
                            invariants = metrics_dict.get("invariants", {})
                            if not isinstance(invariants, dict):
                                return {k: default for k in ["scope_containment_passed", "temporal_validity_passed", "signature_verification_passed", "chain_integrity_passed", "structural_validity_passed", "fail_closed_operation"]}
                            return {
                                "scope_containment_passed": invariants.get("scope_containment_passed", default),
                                "temporal_validity_passed": invariants.get("temporal_validity_passed", default),
                                "signature_verification_passed": invariants.get("signature_verification_passed", default),
                                "chain_integrity_passed": invariants.get("chain_integrity_passed", default),
                                "structural_validity_passed": invariants.get("structural_validity_passed", default),
                                "fail_closed_operation": invariants.get("fail_closed_operation", default)
                            }
                        
                        # Extract all timing metrics safely
                        e2e_timing = get_timing(server_metrics, "e2e_latency")
                        norm_timing = get_timing(server_metrics, "normalization_latency")
                        verif_timing = get_timing(server_metrics, "verification_latency")
                        vro_timing = get_timing(server_metrics, "vro_signing_latency")
                        status_timing = get_timing(server_metrics, "status_fetch_latency")
                        sizes_dict = get_sizes(server_metrics)
                        invariants_dict = get_invariants(server_metrics)
                        
                        # Create metrics object directly (don't use start_request as it resets values)
                        collector.current = VerificationMetrics(
                            request_id=request_id,
                            scenario=scenario,
                            profile=profile,
                            chain_depth=chain_depth,
                            e2e_latency=TimingMetrics(
                                start_time=e2e_timing["start_time"],
                                end_time=e2e_timing["end_time"],
                                duration_ms=e2e_timing["duration_ms"]
                            ),
                            normalization_latency=TimingMetrics(
                                start_time=norm_timing["start_time"],
                                end_time=norm_timing["end_time"],
                                duration_ms=norm_timing["duration_ms"]
                            ),
                            verification_latency=TimingMetrics(
                                start_time=verif_timing["start_time"],
                                end_time=verif_timing["end_time"],
                                duration_ms=verif_timing["duration_ms"]
                            ),
                            vro_signing_latency=TimingMetrics(
                                start_time=vro_timing["start_time"],
                                end_time=vro_timing["end_time"],
                                duration_ms=vro_timing["duration_ms"]
                            ),
                            status_fetch_latency=TimingMetrics(
                                start_time=status_timing["start_time"],
                                end_time=status_timing["end_time"],
                                duration_ms=status_timing["duration_ms"]
                            ),
                            sizes=SizeMetrics(
                                vc_jwt_size_bytes=sizes_dict["vc_jwt_size_bytes"],
                                dg_chain_size_bytes=sizes_dict["dg_chain_size_bytes"],
                                vro_jwt_size_bytes=sizes_dict["vro_jwt_size_bytes"],
                                cvc_serialized_size_bytes=sizes_dict["cvc_serialized_size_bytes"],
                                request_size_bytes=request_size
                            ),
                            invariants=InvariantMetrics(
                                scope_containment_passed=invariants_dict["scope_containment_passed"],
                                temporal_validity_passed=invariants_dict["temporal_validity_passed"],
                                signature_verification_passed=invariants_dict["signature_verification_passed"],
                                chain_integrity_passed=invariants_dict["chain_integrity_passed"],
                                structural_validity_passed=invariants_dict["structural_validity_passed"],
                                fail_closed_operation=invariants_dict["fail_closed_operation"]
                            ),
                            success=server_metrics.get("success", False),
                            error_code=server_metrics.get("error_code", None),
                            vro_hash=server_metrics.get("vro_hash", None),
                            chain_fingerprint=server_metrics.get("chain_fingerprint", None)
                        )
                        
                        # Add anchor metadata if available
                        if require_anchor is not None:
                            collector.current.scenario = f"{scenario}-ANCHOR" if require_anchor else f"{scenario}-NOANCHOR"
                        
                        # End request (adds metric to collector.metrics)
                        collector.end_request()
                    except Exception as e:
                        if int(request_id.split('_')[-1]) <= 3:
                            print(f"  [ERROR] Error copying metrics for {request_id}: {e}")
                            import traceback
                            traceback.print_exc()
                        raise
                else:
                    # Server hasn't completed processing yet
                    return {"success": False, "error": "Server metrics incomplete"}
            else:
                return {"success": False, "error": "No metrics in response"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        # Extract VRO hash if available
        vro_hash = None
        if not response_data:
            try:
                response_data = response.json()
            except:
                pass
        
        if response_data and response.status_code == 200:
            vro_jwt = response_data.get("vro_jwt", "")
            if vro_jwt:
                vro_hash = hash_vro(vro_jwt)
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "vro_hash": vro_hash,
            "chain_depth": chain_depth,
            "profile": profile,
            "require_anchor": require_anchor,
            "error": response_data.get("detail") if response_data and response.status_code != 200 else None
        }
    
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main() -> int:
    """Run batch metrics collection."""
    base_dir = Path(__file__).parent.parent.parent
    requests_dir = base_dir / "fixtures" / "requests" / "batch"
    
    if not requests_dir.exists():
        print(f"[ERROR] Batch requests directory not found: {requests_dir}")
        print("\nGenerate batch requests first:")
        print("  python scripts/batch/generate_batch.py")
        return 1
    
    # Load metadata
    try:
        metadata = load_batch_metadata(requests_dir)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print("\nGenerate batch requests first:")
        print("  python scripts/batch/generate_batch.py")
        return 1
    
    total_requests = metadata.get("total_requests", 0)
    include_anchor = metadata.get("include_anchor", False)
    
    print("=" * 70)
    print("BATCH METRICS COLLECTION")
    print("=" * 70)
    print(f"\nTotal Requests: {total_requests}")
    print(f"Include Anchor: {include_anchor}")
    print(f"Server: {BASE_URL}")
    print("\nStarting metrics collection...")
    print("=" * 70)
    
    # Initialize collector
    collector = get_collector()
    if collector is None:
        print("[ERROR] Metrics collector not available")
        return 1
    
    # Process requests
    start_time = time.time()
    results = []
    
    for i, request_meta in enumerate(metadata.get("requests", [])):
        request_id = request_meta.get("request_id", f"batch_{i:04d}")
        request_file = base_dir / request_meta.get("file", "")
        
        if i < 3:
            print(f"\nProcessing {request_id}...")
        
        result = test_request_with_metrics(request_file, request_meta, collector)
        results.append(result)
        
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  Processed {i + 1}/{total_requests} requests ({rate:.2f} req/s)")
    
    elapsed_time = time.time() - start_time
    
    # Save metrics
    metrics_dir = base_dir / "metrics"
    metrics_dir.mkdir(exist_ok=True)
    
    # Determine output filename based on batch metadata
    batch_has_anchor = metadata.get("include_anchor", False)
    if batch_has_anchor:
        metrics_file = metrics_dir / "collected_metrics_batch_with_anchor.json"
        results_file = metrics_dir / "batch_results_with_anchor.json"
    else:
        metrics_file = metrics_dir / "collected_metrics_batch_no_anchor.json"
        results_file = metrics_dir / "batch_results_no_anchor.json"
    
    # Save collected metrics (convert dataclasses to dicts properly)
    def serialize_metric(metric):
        """Convert VerificationMetrics dataclass to dict."""
        return {
            "request_id": metric.request_id,
            "scenario": metric.scenario,
            "profile": metric.profile,
            "chain_depth": metric.chain_depth,
            "e2e_latency": {
                "start_time": metric.e2e_latency.start_time,
                "end_time": metric.e2e_latency.end_time,
                "duration_ms": metric.e2e_latency.duration_ms
            },
            "normalization_latency": {
                "start_time": metric.normalization_latency.start_time,
                "end_time": metric.normalization_latency.end_time,
                "duration_ms": metric.normalization_latency.duration_ms
            },
            "verification_latency": {
                "start_time": metric.verification_latency.start_time,
                "end_time": metric.verification_latency.end_time,
                "duration_ms": metric.verification_latency.duration_ms
            },
            "vro_signing_latency": {
                "start_time": metric.vro_signing_latency.start_time,
                "end_time": metric.vro_signing_latency.end_time,
                "duration_ms": metric.vro_signing_latency.duration_ms
            },
            "status_fetch_latency": {
                "start_time": metric.status_fetch_latency.start_time,
                "end_time": metric.status_fetch_latency.end_time,
                "duration_ms": metric.status_fetch_latency.duration_ms
            },
            "sizes": {
                "vc_jwt_size_bytes": metric.sizes.vc_jwt_size_bytes,
                "dg_chain_size_bytes": metric.sizes.dg_chain_size_bytes,
                "vro_jwt_size_bytes": metric.sizes.vro_jwt_size_bytes,
                "cvc_serialized_size_bytes": metric.sizes.cvc_serialized_size_bytes,
                "request_size_bytes": metric.sizes.request_size_bytes
            },
            "invariants": {
                "scope_containment_passed": metric.invariants.scope_containment_passed,
                "temporal_validity_passed": metric.invariants.temporal_validity_passed,
                "signature_verification_passed": metric.invariants.signature_verification_passed,
                "chain_integrity_passed": metric.invariants.chain_integrity_passed,
                "structural_validity_passed": metric.invariants.structural_validity_passed,
                "fail_closed_operation": metric.invariants.fail_closed_operation
            },
            "success": metric.success,
            "error_code": metric.error_code,
            "vro_hash": metric.vro_hash,
            "chain_fingerprint": metric.chain_fingerprint,
            "timestamp": metric.timestamp
        }
    
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump([serialize_metric(m) for m in collector.metrics], f, indent=2)
    
    # results_file already determined above based on anchor presence
    successful = sum(1 for r in results if r.get("success", False))
    failed = total_requests - successful
    
    batch_results = {
        "total_requests": total_requests,
        "successful": successful,
        "failed": failed,
        "elapsed_seconds": elapsed_time,
        "requests_per_second": total_requests / elapsed_time if elapsed_time > 0 else 0,
        "include_anchor": include_anchor,
        "results": results
    }
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(batch_results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 70)
    print("BATCH METRICS COLLECTION SUMMARY")
    print("=" * 70)
    print(f"\nTotal Requests: {total_requests}")
    print(f"Successful: {successful} ({successful/total_requests*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total_requests*100:.1f}%)")
    print(f"Elapsed Time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
    print(f"Throughput: {total_requests/elapsed_time:.3f} requests/second")
    
    if include_anchor:
        anchor_results = [r for r in results if r.get("require_anchor") is not None]
        if anchor_results:
            with_anchor = sum(1 for r in anchor_results if r.get("require_anchor") is True)
            without_anchor = sum(1 for r in anchor_results if r.get("require_anchor") is False)
            print(f"\nAnchor Distribution:")
            print(f"  With anchor: {with_anchor} requests")
            print(f"  Without anchor: {without_anchor} requests")
    
    print(f"\n[OK] Metrics collected")
    print(f"  Metrics: {metrics_file}")
    print(f"  Results: {results_file}")
    print(f"\nNext step: Analyze metrics:")
    print(f"  python scripts/analyze_metrics_detailed.py")
    
    return 0 if successful == total_requests else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Metrics collection interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

