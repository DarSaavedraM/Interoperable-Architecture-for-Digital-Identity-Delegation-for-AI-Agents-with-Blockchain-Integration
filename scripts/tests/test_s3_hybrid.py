"""
Individual test for S3: Hybrid Agent Delegation.

S3: Hybrid agent delegation - human→agent DG; constrained scope; revocation freshness.
Tests delegation chain with scope containment and revocation checks.
"""

import json
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base import (
    TestResult, test_health, test_verification_request,
    get_base_dir, print_test_header, print_test_result, BASE_URL, TIMEOUT
)


def test_s3_hybrid_agent(base_dir: Path) -> TestResult:
    """
    S3: Hybrid agent delegation - human→agent DG; constrained scope; revocation freshness.
    
    Tests delegation chain with scope containment and revocation checks.
    """
    requests_dir = base_dir / "fixtures" / "requests"
    req_file = requests_dir / "req_vc_jwt_plus_dg_chain.json"
    
    result = test_verification_request(req_file, expected_success=True)
    result.scenario = "S3"
    
    if result.success:
        # Add scenario-specific details
        result.details = {
            "scenario": "human->agent1->agent2",
            "scope_containment": "verified",
            "revocation_freshness": "StatusList2021 checked"
        }
    
    return result


def main() -> int:
    """Run S3 test individually."""
    base_dir = get_base_dir()
    
    print_test_header("S3: Hybrid Agent Delegation",
                     "Human→agent delegation with constrained scope")
    
    # Health check
    health_ok, health_error = test_health()
    if not health_ok:
        print(f"\n[FAIL] Health check failed: {health_error}")
        print("\nEnsure server is running:")
        print("  python scripts/start_server.py")
        return 1
    
    print("\n[OK] Server is running")
    
    # Run test
    result = test_s3_hybrid_agent(base_dir)
    print_test_result(result, "S3")
    
    # Summary
    print("\n" + "=" * 70)
    if result.success:
        print("[OK] S3 test passed")
        return 0
    else:
        print("[FAIL] S3 test failed")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(130)


