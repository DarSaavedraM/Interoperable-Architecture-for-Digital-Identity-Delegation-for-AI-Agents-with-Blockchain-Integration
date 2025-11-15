"""
Individual test for S2: SSI Flow.

S2: SSI flow - VC-LD(BBS+) with StatusList2021 + DG-LD or DG-SD-JWT.
Tests format independence through VC-LD normalization to CVC.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base import (
    TestResult, test_health, test_verification_request,
    get_base_dir, print_test_header, print_test_result
)


def test_s2_ssi_flow(base_dir: Path) -> TestResult:
    """
    S2: SSI flow - VC-LD(BBS+) with StatusList2021 + DG-LD or DG-SD-JWT.
    
    Tests format independence through VC-LD normalization to CVC.
    Full BBS+ signature verification requires LD-Proof libraries.
    """
    requests_dir = base_dir / "fixtures" / "requests"
    
    # Try both DG formats
    req_dgld = requests_dir / "req_s2_ssi_dgld.json"
    req_dgsdjwt = requests_dir / "req_s2_ssi_dgsdjwt.json"
    
    # Test with DG-LD first, fallback to DG-SD-JWT
    req_file = req_dgld if req_dgld.exists() else req_dgsdjwt
    
    result = test_verification_request(req_file, expected_success=True)
    result.scenario = "S2"
    
    if result.success:
        result.limitation = "VC-LD normalization to CVC works; full BBS+ verification requires LD-Proof libraries"
    
    return result


def main() -> int:
    """Run S2 test individually."""
    base_dir = get_base_dir()
    
    print_test_header("S2: SSI Flow (VC-LD + DG)",
                     "SSI flow with VC-LD and delegation chain")
    
    # Health check
    health_ok, health_error = test_health()
    if not health_ok:
        print(f"\n[FAIL] Health check failed: {health_error}")
        print("\nEnsure server is running:")
        print("  python scripts/start_server.py")
        return 1
    
    print("\n[OK] Server is running")
    
    # Run test
    result = test_s2_ssi_flow(base_dir)
    print_test_result(result, "S2")
    
    # Summary
    print("\n" + "=" * 70)
    if result.success:
        print("[OK] S2 test passed")
        return 0
    else:
        print("[FAIL] S2 test failed")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(130)


