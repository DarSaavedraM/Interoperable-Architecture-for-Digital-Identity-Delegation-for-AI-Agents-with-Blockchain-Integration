"""
Individual test for S1: Federated Flow.

S1: Federated flow - VC-JWT + SD-JWT with DG; OIDC4VP presentation.
Tests VC-JWT with delegation chain. OIDC4VP normalization is demonstrated
but full OIDC4VP flow (authorization request/response) is not implemented.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base import (
    TestResult, test_health, test_verification_request, 
    get_base_dir, print_test_header, print_test_result
)


def test_s1_federated_flow(base_dir: Path) -> TestResult:
    """
    S1: Federated flow - VC-JWT + SD-JWT with DG; OIDC4VP presentation.
    
    Tests VC-JWT with delegation chain. OIDC4VP normalization is demonstrated
    but full OIDC4VP flow (authorization request/response) is not implemented.
    """
    requests_dir = base_dir / "fixtures" / "requests"
    req_file = requests_dir / "req_vc_jwt_plus_dg_chain.json"
    
    result = test_verification_request(req_file, expected_success=True)
    result.scenario = "S1"
    
    if result.success:
        result.limitation = "OIDC4VP full flow not implemented; normalization demonstrated via /verify/oidc4vp endpoint"
    
    return result


def main() -> int:
    """Run S1 test individually."""
    base_dir = get_base_dir()
    
    print_test_header("S1: Federated Flow (VC-JWT + DG)", 
                     "Federated flow with VC-JWT and delegation chain")
    
    # Health check
    health_ok, health_error = test_health()
    if not health_ok:
        print(f"\n[FAIL] Health check failed: {health_error}")
        print("\nEnsure server is running:")
        print("  python scripts/start_server.py")
        return 1
    
    print("\n[OK] Server is running")
    
    # Run test
    result = test_s1_federated_flow(base_dir)
    print_test_result(result, "S1")
    
    # Summary
    print("\n" + "=" * 70)
    if result.success:
        print("[OK] S1 test passed")
        return 0
    else:
        print("[FAIL] S1 test failed")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(130)


