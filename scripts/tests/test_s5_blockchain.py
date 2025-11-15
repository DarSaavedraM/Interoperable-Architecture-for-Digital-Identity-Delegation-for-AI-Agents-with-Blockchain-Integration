"""
Individual test for S5: Blockchain Anchor.

S5: Blockchain anchor - tests delegation chain anchoring with and without anchor requirement.
Tests that chains are properly anchored when require_anchor=true and verified when already anchored.
"""

import json
import sys
import requests
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base import (
    TestResult, test_health, test_verification_request,
    get_base_dir, print_test_header, print_test_result, BASE_URL, TIMEOUT
)


def test_without_anchor() -> TestResult:
    """Test verification without anchor requirement (default behavior)."""
    base_dir = get_base_dir()
    request_file = base_dir / "fixtures" / "requests" / "req_vc_jwt_plus_dg_chain.json"
    
    if not request_file.exists():
        return TestResult(
            success=False,
            error_code="FILE_NOT_FOUND",
            details={"file": str(request_file)},
            scenario="S5"
        )
    
    result = test_verification_request(request_file, expected_success=True)
    result.scenario = "S5"
    return result


def test_with_anchor() -> TestResult:
    """Test verification with anchor requirement."""
    base_dir = get_base_dir()
    
    # Create a policy with require_anchor: true
    policy_with_anchor = {
        "id": "P-001-ANCHOR",
        "trusted_issuers": ["did:example:bank"],
        "alg_allowlist": ["EdDSA"],
        "holder_binding_required": True,
        "max_delegation_depth": 3,
        "status_ttl_seconds": 120,
        "clock_skew_seconds": 5,
        "require_anchor": True,  # Enable anchor requirement
        "status_required": True
    }
    
    # Save temporary policy with normalized filename (P-001-ANCHOR -> P001ANCHOR)
    temp_policy_path = base_dir / "fixtures" / "policy_P001ANCHOR.json"
    temp_policy_path.write_text(json.dumps(policy_with_anchor, indent=2))
    
    try:
        # Load request
        request_file = base_dir / "fixtures" / "requests" / "req_vc_jwt_plus_dg_chain.json"
        if not request_file.exists():
            return TestResult(
                success=False,
                error_code="FILE_NOT_FOUND",
                details={"file": str(request_file)},
                scenario="S5"
            )
        
        # First request: should anchor the chain
        result1 = test_verification_request(request_file, expected_success=True, policy_id="P-001-ANCHOR")
        if not result1.success:
            return result1
        
        # Second request: should verify existing anchor
        result2 = test_verification_request(request_file, expected_success=True, policy_id="P-001-ANCHOR")
        
        if result2.success:
            return TestResult(
                success=True,
                details={"first_anchor": True, "second_verify": True},
                scenario="S5"
            )
        else:
            return result2
    
    finally:
        # Cleanup: remove temporary policy
        if temp_policy_path.exists():
            temp_policy_path.unlink()


def test_anchor_storage() -> TestResult:
    """Test that anchor storage file is created."""
    base_dir = get_base_dir()
    anchor_file = base_dir / "fixtures" / "anchors" / "blockchain_anchors.json"
    
    if anchor_file.exists():
        with open(anchor_file, 'r') as f:
            data = json.load(f)
        
        anchors = data.get("anchors", {})
        chain = data.get("chain", [])
        
        return TestResult(
            success=True,
            details={
                "anchors_stored": len(anchors),
                "chain_length": len(chain)
            },
            scenario="S5"
        )
    else:
        return TestResult(
            success=False,
            error_code="STORAGE_NOT_FOUND",
            details={"file": str(anchor_file)},
            scenario="S5"
        )


def test_s5_blockchain() -> Dict[str, TestResult]:
    """Run all S5 blockchain tests."""
    results = {}
    
    # Test without anchor
    results["without_anchor"] = test_without_anchor()
    
    # Test with anchor
    results["with_anchor"] = test_with_anchor()
    
    # Test storage
    results["anchor_storage"] = test_anchor_storage()
    
    return results


def main() -> int:
    """Run S5 test individually."""
    base_dir = get_base_dir()
    
    print_test_header("S5: Blockchain Anchor",
                     "Delegation chain anchoring with and without anchor requirement")
    
    # Health check
    health_ok, health_error = test_health()
    if not health_ok:
        print(f"\n[FAIL] Health check failed: {health_error}")
        print("\nEnsure server is running:")
        print("  python scripts/start_server.py")
        return 1
    
    print("\n[OK] Server is running")
    
    # Run tests
    results = test_s5_blockchain()
    
    print("\n--- Test: Without Anchor ---")
    print_test_result(results["without_anchor"], "S5-without_anchor")
    
    print("\n--- Test: With Anchor ---")
    print_test_result(results["with_anchor"], "S5-with_anchor")
    
    print("\n--- Test: Anchor Storage ---")
    print_test_result(results["anchor_storage"], "S5-anchor_storage")
    
    # Summary
    print("\n" + "=" * 70)
    all_passed = all(r.success for r in results.values())
    
    if all_passed:
        print("[OK] All S5 blockchain tests passed")
        return 0
    else:
        print("[FAIL] Some S5 blockchain tests failed")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(130)


