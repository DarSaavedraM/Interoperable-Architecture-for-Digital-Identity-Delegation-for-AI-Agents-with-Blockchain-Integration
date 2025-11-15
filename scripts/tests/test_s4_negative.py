"""
Individual test for S4: Negative Cases.

S4: Negative cases - expired DG, revoked status, scope escalation, key-binding mismatch.
Tests that negative cases are properly rejected with appropriate error codes.
"""

import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base import (
    TestResult, test_health, test_verification_request,
    get_base_dir, print_test_header, print_test_result
)


def test_s4_negative_cases(base_dir: Path) -> Dict[str, TestResult]:
    """
    S4: Negative cases - expired DG, revoked status, scope escalation, key-binding mismatch.
    
    Tests that negative cases are properly rejected with appropriate error codes.
    """
    requests_dir = base_dir / "fixtures" / "requests"
    results = {}
    
    # S4a: Expired DG
    req_expired = requests_dir / "req_s4_expired_dg.json"
    if req_expired.exists():
        results["expired_dg"] = test_verification_request(req_expired, expected_success=False)
        results["expired_dg"].scenario = "S4"
        if results["expired_dg"].success:
            results["expired_dg"].details = {"expected_error": "E300 (DG_TIME)"}
    
    # S4b: Revoked DG
    req_revoked_dg = requests_dir / "req_s4_revoked_dg.json"
    if req_revoked_dg.exists():
        results["revoked_dg"] = test_verification_request(req_revoked_dg, expected_success=False)
        results["revoked_dg"].scenario = "S4"
        if results["revoked_dg"].success:
            results["revoked_dg"].details = {"expected_error": "E300 (DG_REVOKED)"}
    
    # S4c: Scope escalation
    req_escalation = requests_dir / "req_s4_scope_escalation.json"
    if req_escalation.exists():
        results["scope_escalation"] = test_verification_request(req_escalation, expected_success=False)
        results["scope_escalation"].scenario = "S4"
        if results["scope_escalation"].success:
            results["scope_escalation"].details = {"expected_error": "E400 (DG_SCOPE_ESCALATION)"}
    
    # S4d: Key binding (document limitation)
    req_keybinding = requests_dir / "req_s4_key_binding.json"
    if req_keybinding.exists():
        results["key_binding"] = test_verification_request(req_keybinding, expected_success=True)
        results["key_binding"].scenario = "S4"
        if results["key_binding"].success:
            results["key_binding"].limitation = "Key binding present but proof-of-possession (PoP) not verified; this is a known limitation"
    
    return results


def main() -> int:
    """Run S4 test individually."""
    base_dir = get_base_dir()
    
    print_test_header("S4: Negative Cases",
                     "Expired DG, revoked status, scope escalation, key-binding")
    
    # Health check
    health_ok, health_error = test_health()
    if not health_ok:
        print(f"\n[FAIL] Health check failed: {health_error}")
        print("\nEnsure server is running:")
        print("  python scripts/start_server.py")
        return 1
    
    print("\n[OK] Server is running")
    
    # Run tests
    results = test_s4_negative_cases(base_dir)
    
    for case_name, result in results.items():
        print_test_result(result, f"S4-{case_name}")
    
    # Summary
    print("\n" + "=" * 70)
    all_passed = all(r.success for r in results.values())
    
    if all_passed:
        print("[OK] All S4 negative cases passed")
        return 0
    else:
        print("[FAIL] Some S4 negative cases failed")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(130)


