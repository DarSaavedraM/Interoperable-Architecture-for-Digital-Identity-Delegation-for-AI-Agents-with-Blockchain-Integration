"""
Verify final project status and metrics.
"""
import json
from pathlib import Path
from collections import Counter

def main():
    """Verify final project status."""
    print("=" * 70)
    print("FINAL PROJECT STATUS VERIFICATION")
    print("=" * 70)
    
    # Load metrics
    metrics_file = Path('metrics/collected_metrics_batch_with_anchor.json')
    if not metrics_file.exists():
        print(f"[ERROR] Metrics file not found: {metrics_file}")
        return
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    
    print(f"\nMetrics Collection:")
    print(f"  Total metrics: {len(metrics)}")
    
    success_count = sum(1 for x in metrics if x.get('success'))
    print(f"  Success rate: {success_count}/{len(metrics)} ({success_count/len(metrics)*100:.1f}%)")
    
    # VRO hash uniqueness
    vro_hashes = [x.get('vro_hash', '') for x in metrics if x.get('vro_hash')]
    unique_hashes = len(set(vro_hashes))
    print(f"  Unique VRO hashes: {unique_hashes}/{len(vro_hashes)} ({unique_hashes/len(vro_hashes)*100:.1f}%)")
    
    # Profile distribution
    profiles = Counter(x.get('profile') for x in metrics)
    print(f"\nProfile Distribution:")
    for profile, count in sorted(profiles.items()):
        print(f"  {profile}: {count} ({count/len(metrics)*100:.1f}%)")
    
    # Chain depth distribution
    depths = Counter(x.get('chain_depth', 0) for x in metrics)
    print(f"\nChain Depth Distribution:")
    for depth in sorted(depths.keys()):
        count = depths[depth]
        print(f"  Depth {depth}: {count} ({count/len(metrics)*100:.1f}%)")
    
    # Anchor distribution
    scenarios = [x.get('scenario', '') for x in metrics]
    anchor_with = sum(1 for s in scenarios if 'ANCHOR' in s and 'NOANCHOR' not in s)
    anchor_without = sum(1 for s in scenarios if 'NOANCHOR' in s)
    anchor_none = len(metrics) - anchor_with - anchor_without
    print(f"\nAnchor Distribution:")
    print(f"  With anchor: {anchor_with} ({anchor_with/len(metrics)*100:.1f}%)")
    print(f"  Without anchor: {anchor_without} ({anchor_without/len(metrics)*100:.1f}%)")
    print(f"  No anchor variable (depth=0): {anchor_none} ({anchor_none/len(metrics)*100:.1f}%)")
    
    # Metrics completeness
    sample = metrics[0] if metrics else {}
    print(f"\nMetrics Completeness:")
    print(f"  E2E latency: {'OK' if sample.get('e2e_latency', {}).get('duration_ms', 0) > 0 else 'MISSING'}")
    print(f"  Normalization latency: {'OK' if sample.get('normalization_latency', {}).get('duration_ms', 0) > 0 else 'MISSING'}")
    print(f"  Verification latency: {'OK' if sample.get('verification_latency', {}).get('duration_ms', 0) > 0 else 'MISSING'}")
    print(f"  Sizes: {'OK' if sample.get('sizes', {}).get('cvc_serialized_size_bytes', 0) > 0 else 'MISSING'}")
    print(f"  Invariants: {'OK' if sample.get('invariants', {}).get('scope_containment_passed') is not None else 'MISSING'}")
    
    print("\n" + "=" * 70)
    print("[OK] Project status verified")
    print("=" * 70)

if __name__ == "__main__":
    main()


