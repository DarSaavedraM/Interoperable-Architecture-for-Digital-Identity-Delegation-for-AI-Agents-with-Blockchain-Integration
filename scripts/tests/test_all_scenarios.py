"""
Conjoint test for all verification scenarios (S1-S5).

This script runs all test scenarios including blockchain anchor tests.
Can be configured to include/exclude specific scenarios.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base import test_health, get_base_dir, print_test_header
from tests.test_s1_federated import test_s1_federated_flow
from tests.test_s2_ssi import test_s2_ssi_flow
from tests.test_s3_hybrid import test_s3_hybrid_agent
from tests.test_s4_negative import test_s4_negative_cases
from tests.test_s5_blockchain import test_s5_blockchain


def main() -> int:
    """Run all test scenarios."""
    parser = argparse.ArgumentParser(
        description="Run all verification scenario tests (S1-S5)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all scenarios including blockchain
  python scripts/tests/test_all_scenarios.py --include-blockchain
  
  # Run only specific scenarios
  python scripts/tests/test_all_scenarios.py --scenarios S1,S2,S5
  
  # Run all except blockchain
  python scripts/tests/test_all_scenarios.py
        """
    )
    parser.add_argument(
        "--include-blockchain",
        action="store_true",
        help="Include S5 blockchain anchor tests (default: False)"
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        help="Comma-separated list of scenarios to run (e.g., S1,S2,S5). If not specified, runs S1-S4 (and S5 if --include-blockchain)"
    )
    
    args = parser.parse_args()
    
    base_dir = get_base_dir()
    
    print("=" * 70)
    print("VERIFICATION SCENARIOS TEST SUITE")
    print("=" * 70)
    
    # Health check
    health_ok, health_error = test_health()
    if not health_ok:
        print(f"\n[FAIL] Health check failed: {health_error}")
        print("\nEnsure server is running:")
        print("  python scripts/start_server.py")
        return 1
    
    print("\n[OK] Server is running")
    
    # Determine which scenarios to run
    if args.scenarios:
        scenarios_to_run = [s.strip().upper() for s in args.scenarios.split(",")]
    else:
        scenarios_to_run = ["S1", "S2", "S3", "S4"]
        if args.include_blockchain:
            scenarios_to_run.append("S5")
    
    results = {}
    
    # S1: Federated flow
    if "S1" in scenarios_to_run:
        print("\n" + "-" * 70)
        print("S1: Federated Flow (VC-JWT + DG)")
        print("-" * 70)
        from tests.base import print_test_result
        s1_result = test_s1_federated_flow(base_dir)
        print_test_result(s1_result, "S1")
        results["S1"] = s1_result
    
    # S2: SSI flow
    if "S2" in scenarios_to_run:
        print("\n" + "-" * 70)
        print("S2: SSI Flow (VC-LD + DG)")
        print("-" * 70)
        from tests.base import print_test_result
        s2_result = test_s2_ssi_flow(base_dir)
        print_test_result(s2_result, "S2")
        results["S2"] = s2_result
    
    # S3: Hybrid agent
    if "S3" in scenarios_to_run:
        print("\n" + "-" * 70)
        print("S3: Hybrid Agent Delegation")
        print("-" * 70)
        from tests.base import print_test_result
        s3_result = test_s3_hybrid_agent(base_dir)
        print_test_result(s3_result, "S3")
        results["S3"] = s3_result
    
    # S4: Negative cases
    if "S4" in scenarios_to_run:
        print("\n" + "-" * 70)
        print("S4: Negative Cases")
        print("-" * 70)
        from tests.base import print_test_result
        s4_results = test_s4_negative_cases(base_dir)
        
        for case_name, result in s4_results.items():
            print_test_result(result, f"S4-{case_name}")
        
        # Aggregate S4 results
        s4_all_passed = all(r.success for r in s4_results.values())
        results["S4"] = type('obj', (object,), {
            'success': s4_all_passed,
            'scenario': 'S4',
            'details': {k: r.success for k, r in s4_results.items()}
        })()
    
    # S5: Blockchain anchor
    if "S5" in scenarios_to_run:
        print("\n" + "-" * 70)
        print("S5: Blockchain Anchor")
        print("-" * 70)
        from tests.base import print_test_result
        s5_results = test_s5_blockchain()
        
        print("\n--- Test: Without Anchor ---")
        print_test_result(s5_results["without_anchor"], "S5-without_anchor")
        
        print("\n--- Test: With Anchor ---")
        print_test_result(s5_results["with_anchor"], "S5-with_anchor")
        
        print("\n--- Test: Anchor Storage ---")
        print_test_result(s5_results["anchor_storage"], "S5-anchor_storage")
        
        # Aggregate S5 results
        s5_all_passed = all(r.success for r in s5_results.values())
        results["S5"] = type('obj', (object,), {
            'success': s5_all_passed,
            'scenario': 'S5',
            'details': {k: r.success for k, r in s5_results.items()}
        })()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for scenario in ["S1", "S2", "S3", "S4", "S5"]:
        if scenario in results:
            result = results[scenario]
            status = "[PASS]" if result.success else "[FAIL]"
            print(f"{scenario}: {status}")
    
    all_passed = all(r.success for r in results.values())
    
    if all_passed:
        print("\n[OK] All scenarios passed")
        return 0
    else:
        print("\n[FAIL] Some scenarios failed")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(130)


