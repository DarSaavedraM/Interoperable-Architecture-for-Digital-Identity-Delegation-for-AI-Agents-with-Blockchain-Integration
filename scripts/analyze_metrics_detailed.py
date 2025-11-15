"""
Detailed verification metrics analysis.
Run: python scripts/analyze_metrics_detailed.py

Generates analysis report and saves to metrics/reports/ directory.
Also prints to console for immediate viewing.
"""

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Any
import math
from datetime import datetime
import sys

def percentile(data: List[float], p: float) -> float:
    """Calculate percentile."""
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1

def stats_summary(data: List[float], name: str) -> Dict[str, float]:
    """Calculate comprehensive statistics."""
    if not data:
        return {}
    return {
        'count': len(data),
        'mean': statistics.mean(data),
        'median': statistics.median(data),
        'std': statistics.stdev(data) if len(data) > 1 else 0,
        'min': min(data),
        'max': max(data),
        'p25': percentile(data, 25),
        'p75': percentile(data, 75),
        'p90': percentile(data, 90),
        'p95': percentile(data, 95),
        'p99': percentile(data, 99),
    }

def analyze_metrics():
    """Perform detailed metrics analysis and save to report file."""
    
    # Load metrics (use the batch with anchor as it includes all requests)
    metrics_file = Path('metrics/collected_metrics_batch_with_anchor.json')
    if not metrics_file.exists():
        # Fallback to default name
        metrics_file = Path('metrics/collected_metrics_batch.json')
    
    if not metrics_file.exists():
        print(f"[ERROR] Metrics file not found. Expected: {metrics_file}")
        print("\nGenerate and collect batch metrics first:")
        print("  python scripts/batch/generate_batch.py")
        print("  python scripts/batch/run_batch_metrics.py")
        return
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    
    # Create output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = Path('metrics/reports')
    reports_dir.mkdir(exist_ok=True)
    output_file = reports_dir / f"metrics_analysis_{timestamp}.md"
    
    # Capture stdout to both console and file
    class TeeOutput:
        def __init__(self, file_path: Path):
            self.file = open(file_path, 'w', encoding='utf-8')
            self.stdout = sys.stdout
            
        def write(self, text):
            self.stdout.write(text)  # Print to console
            self.file.write(text)     # Write to file
            
        def flush(self):
            self.stdout.flush()
            self.file.flush()
            
        def close(self):
            self.file.close()
    
    # Redirect stdout to capture all output
    tee = TeeOutput(output_file)
    sys.stdout = tee
    
    try:
        # Write header
        print("# Detailed Verification Metrics Analysis\n")
        print(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"**Total Requests:** {len(metrics)}\n")
        print(f"**Metrics Source:** {metrics_file}\n\n")
        print("---\n\n")
        
        # ========================================================================
        # 1. GENERAL LATENCY STATISTICS
        # ========================================================================
        print("## 1. Latency Statistics (End-to-End)\n\n")
    
        e2e_all = [m['e2e_latency']['duration_ms'] for m in metrics]
        e2e_stats = stats_summary(e2e_all, "E2E")
        print(f"- **Count:** {e2e_stats['count']}\n")
        print(f"- **Mean:** {e2e_stats['mean']:.3f} ms\n")
        print(f"- **Median:** {e2e_stats['median']:.3f} ms\n")
        print(f"- **Std Dev:** {e2e_stats['std']:.3f} ms\n")
        print(f"- **Min:** {e2e_stats['min']:.3f} ms\n")
        print(f"- **Max:** {e2e_stats['max']:.3f} ms\n")
        print(f"- **P25:** {e2e_stats['p25']:.3f} ms\n")
        print(f"- **P75:** {e2e_stats['p75']:.3f} ms\n")
        print(f"- **P90:** {e2e_stats['p90']:.3f} ms\n")
        print(f"- **P95:** {e2e_stats['p95']:.3f} ms\n")
        print(f"- **P99:** {e2e_stats['p99']:.3f} ms\n\n")
    
        # ========================================================================
        # 2. LATENCY COMPONENT ANALYSIS
        # ========================================================================
        print("\n" + "=" * 80)
        print("## LATENCY COMPONENT ANALYSIS\n\n")
        print("---\n\n")
    
        # Normalization latency
        norm_all = [m['normalization_latency']['duration_ms'] for m in metrics 
                    if m['normalization_latency']['duration_ms'] > 0]
        norm_stats = stats_summary(norm_all, "Normalization")
        print(f"\nNormalization Latency ({len(norm_all)}/{len(metrics)} non-zero):\n")
        print(f"  Mean:     {norm_stats['mean']:.3f} ms\n")
        print(f"  Median:   {norm_stats['median']:.3f} ms\n")
        print(f"  Std Dev:  {norm_stats['std']:.3f} ms\n")
        print(f"  Min:      {norm_stats['min']:.3f} ms\n")
        print(f"  Max:      {norm_stats['max']:.3f} ms\n")
        print(f"  P95:      {norm_stats['p95']:.3f} ms\n")
    
        # Verification latency
        verif_all = [m['verification_latency']['duration_ms'] for m in metrics 
                     if m['verification_latency']['duration_ms'] > 0]
        verif_stats = stats_summary(verif_all, "Verification")
        print(f"\nVerification Latency ({len(verif_all)}/{len(metrics)} non-zero):\n")
        print(f"  Mean:     {verif_stats['mean']:.3f} ms\n")
        print(f"  Median:   {verif_stats['median']:.3f} ms\n")
        print(f"  Std Dev:  {verif_stats['std']:.3f} ms\n")
        print(f"  Min:      {verif_stats['min']:.3f} ms\n")
        print(f"  Max:      {verif_stats['max']:.3f} ms\n")
        print(f"  P95:      {verif_stats['p95']:.3f} ms\n")
    
        # VRO Signing latency
        vro_signing_all = [m['vro_signing_latency']['duration_ms'] for m in metrics 
                           if m['vro_signing_latency']['duration_ms'] > 0]
        vro_stats = stats_summary(vro_signing_all, "VRO Signing")
        print(f"\nVRO Signing Latency ({len(vro_signing_all)}/{len(metrics)} non-zero):\n")
        print(f"  Mean:     {vro_stats['mean']:.3f} ms\n")
        print(f"  Median:   {vro_stats['median']:.3f} ms\n")
        print(f"  P95:      {vro_stats['p95']:.3f} ms\n")
    
        # Status fetch latency
        status_all = [m['status_fetch_latency']['duration_ms'] for m in metrics 
                      if m['status_fetch_latency']['duration_ms'] > 0]
        status_stats = stats_summary(status_all, "Status Fetch")
        print(f"\nStatus Fetch Latency ({len(status_all)}/{len(metrics)} non-zero):\n")
        print(f"  Mean:     {status_stats['mean']:.3f} ms\n")
        print(f"  Median:   {status_stats['median']:.3f} ms\n")
        print(f"  P95:      {status_stats['p95']:.3f} ms\n")
    
        # Overhead analysis
        print(f"\nOverhead Analysis:\n")
        overheads = []
        for m in metrics:
            norm = m['normalization_latency']['duration_ms']
            verif = m['verification_latency']['duration_ms']
            vro = m['vro_signing_latency']['duration_ms']
            status = m['status_fetch_latency']['duration_ms']
            e2e = m['e2e_latency']['duration_ms']
            components = norm + verif + vro + status
            if e2e > 0:
                overhead = e2e - components
                overheads.append(overhead)
        if overheads:
            overhead_stats = stats_summary(overheads, "Overhead")
            print(f"  Mean overhead (E2E - components): {overhead_stats['mean']:.3f} ms\n")
            print(f"  Median overhead: {overhead_stats['median']:.3f} ms\n")
            print(f"  Overhead % of E2E: {overhead_stats['mean']/e2e_stats['mean']*100:.1f}%\n")
    
        # ========================================================================
        # 3. FORMAT INDEPENDENCE ANALYSIS (VC-JWT vs VC-LD)
        # ========================================================================
        print("\n" + "=" * 80)
        print("## FORMAT INDEPENDENCE ANALYSIS (VC-JWT vs VC-LD)\n\n")
        print("---\n\n")
    
        by_profile = defaultdict(list)
        for m in metrics:
            by_profile[m['profile']].append(m)
    
        profile_stats = {}
        for profile, profile_metrics in sorted(by_profile.items()):
            profile_e2e = [m['e2e_latency']['duration_ms'] for m in profile_metrics]
            profile_norm = [m['normalization_latency']['duration_ms'] for m in profile_metrics 
                           if m['normalization_latency']['duration_ms'] > 0]
            profile_verif = [m['verification_latency']['duration_ms'] for m in profile_metrics 
                            if m['verification_latency']['duration_ms'] > 0]
            profile_cvc = [m['sizes']['cvc_serialized_size_bytes'] for m in profile_metrics
                          if m['sizes']['cvc_serialized_size_bytes'] > 0]
        
            profile_stats[profile] = {
                'count': len(profile_metrics),
                'e2e': stats_summary(profile_e2e, f"{profile}-E2E"),
                'norm': stats_summary(profile_norm, f"{profile}-Norm") if profile_norm else {},
                'verif': stats_summary(profile_verif, f"{profile}-Verif") if profile_verif else {},
                'cvc_size': stats_summary(profile_cvc, f"{profile}-CVC") if profile_cvc else {}
            }
        
            print(f"\n{profile} ({len(profile_metrics)} requests, {len(profile_metrics)/len(metrics)*100:.1f}%):\n")
            print(f"  E2E:      mean={profile_stats[profile]['e2e']['mean']:.3f}ms, median={profile_stats[profile]['e2e']['median']:.3f}ms, P95={profile_stats[profile]['e2e']['p95']:.3f}ms\n")
            if profile_stats[profile]['norm']:
                print(f"  Norm:     mean={profile_stats[profile]['norm']['mean']:.3f}ms, median={profile_stats[profile]['norm']['median']:.3f}ms, P95={profile_stats[profile]['norm']['p95']:.3f}ms\n")
            if profile_stats[profile]['verif']:
                print(f"  Verif:    mean={profile_stats[profile]['verif']['mean']:.3f}ms, median={profile_stats[profile]['verif']['median']:.3f}ms, P95={profile_stats[profile]['verif']['p95']:.3f}ms\n")
            if profile_stats[profile]['cvc_size']:
                print(f"  CVC Size: mean={profile_stats[profile]['cvc_size']['mean']:.0f} bytes, median={profile_stats[profile]['cvc_size']['median']:.0f} bytes\n")
    
        # Format Independence Comparison
        if 'VC-JWT' in profile_stats and 'VC-LD' in profile_stats:
            print(f"\nFormat Independence Comparison:\n")
            vcjwt_e2e = profile_stats['VC-JWT']['e2e']['mean']
            vcld_e2e = profile_stats['VC-LD']['e2e']['mean']
            e2e_diff = abs(vcjwt_e2e - vcld_e2e)
            e2e_diff_pct = (e2e_diff / min(vcjwt_e2e, vcld_e2e)) * 100
            print(f"  E2E Latency Difference: {e2e_diff:.3f}ms ({e2e_diff_pct:.1f}% of smaller value)\n")
        
            if profile_stats['VC-JWT']['norm'] and profile_stats['VC-LD']['norm']:
                vcjwt_norm = profile_stats['VC-JWT']['norm']['mean']
                vcld_norm = profile_stats['VC-LD']['norm']['mean']
                norm_diff = abs(vcjwt_norm - vcld_norm)
                norm_diff_pct = (norm_diff / min(vcjwt_norm, vcld_norm)) * 100
                print(f"  Normalization Latency Difference: {norm_diff:.3f}ms ({norm_diff_pct:.1f}% of smaller value)\n")
        
            if profile_stats['VC-JWT']['verif'] and profile_stats['VC-LD']['verif']:
                vcjwt_verif = profile_stats['VC-JWT']['verif']['mean']
                vcld_verif = profile_stats['VC-LD']['verif']['mean']
                verif_diff = abs(vcjwt_verif - vcld_verif)
                verif_diff_pct = (verif_diff / min(vcjwt_verif, vcld_verif)) * 100
                print(f"  Verification Latency Difference: {verif_diff:.3f}ms ({verif_diff_pct:.1f}% of smaller value)\n")
        
            # Format Independence Index (simplified: smaller difference = more independent)
            if profile_stats['VC-JWT']['norm'] and profile_stats['VC-LD']['norm']:
                norm_std = statistics.stdev([profile_stats['VC-JWT']['norm']['mean'], profile_stats['VC-LD']['norm']['mean']])
                norm_mean = statistics.mean([profile_stats['VC-JWT']['norm']['mean'], profile_stats['VC-LD']['norm']['mean']])
                format_independence = 1 - (norm_std / norm_mean) if norm_mean > 0 else 0
                print(f"  Normalization Independence Index: {format_independence:.3f} (1.0 = perfect independence)\n")
    
        # ========================================================================
        # 4. SCALABILITY ANALYSIS (Chain Depth Impact)
        # ========================================================================
        print("\n" + "=" * 80)
        print("## SCALABILITY ANALYSIS (Chain Depth Impact)\n\n")
        print("---\n\n")
    
        by_depth = defaultdict(list)
        for m in metrics:
            by_depth[m['chain_depth']].append(m)
    
        depth_stats = {}
        for depth in sorted(by_depth.keys()):
            depth_metrics = by_depth[depth]
            depth_e2e = [m['e2e_latency']['duration_ms'] for m in depth_metrics]
            depth_norm = [m['normalization_latency']['duration_ms'] for m in depth_metrics 
                         if m['normalization_latency']['duration_ms'] > 0]
            depth_verif = [m['verification_latency']['duration_ms'] for m in depth_metrics 
                          if m['verification_latency']['duration_ms'] > 0]
            depth_cvc = [m['sizes']['cvc_serialized_size_bytes'] for m in depth_metrics 
                        if m['sizes']['cvc_serialized_size_bytes'] > 0]
        
            depth_stats[depth] = {
                'count': len(depth_metrics),
                'e2e': stats_summary(depth_e2e, f"Depth{depth}-E2E"),
                'norm': stats_summary(depth_norm, f"Depth{depth}-Norm") if depth_norm else {},
                'verif': stats_summary(depth_verif, f"Depth{depth}-Verif") if depth_verif else {},
                'cvc_size': stats_summary(depth_cvc, f"Depth{depth}-CVC") if depth_cvc else {}
            }
        
            print(f"\nChain Depth {depth} ({len(depth_metrics)} requests, {len(depth_metrics)/len(metrics)*100:.1f}%):\n")
            print(f"  E2E:      mean={depth_stats[depth]['e2e']['mean']:.3f}ms, median={depth_stats[depth]['e2e']['median']:.3f}ms, P95={depth_stats[depth]['e2e']['p95']:.3f}ms\n")
            if depth_stats[depth]['norm']:
                print(f"  Norm:     mean={depth_stats[depth]['norm']['mean']:.3f}ms, median={depth_stats[depth]['norm']['median']:.3f}ms\n")
            if depth_stats[depth]['verif']:
                print(f"  Verif:    mean={depth_stats[depth]['verif']['mean']:.3f}ms, median={depth_stats[depth]['verif']['median']:.3f}ms, P95={depth_stats[depth]['verif']['p95']:.3f}ms\n")
            if depth_stats[depth]['cvc_size']:
                print(f"  CVC Size: mean={depth_stats[depth]['cvc_size']['mean']:.0f} bytes, median={depth_stats[depth]['cvc_size']['median']:.0f} bytes\n")
    
        # Scalability Analysis: Verification time per chain depth
        if 0 in depth_stats and depth_stats[0]['verif']:
            base_verif = depth_stats[0]['verif']['mean']
            print(f"\nScalability Metrics (relative to depth=0):\n")
            for depth in sorted([d for d in depth_stats.keys() if d > 0]):
                if depth_stats[depth]['verif']:
                    verif_time = depth_stats[depth]['verif']['mean']
                    ratio = verif_time / base_verif if base_verif > 0 else 0
                    print(f"  Depth {depth}: {verif_time:.3f}ms ({ratio:.2f}x depth=0)\n")
        
            # Estimate complexity: linear vs quadratic
            if all(d in depth_stats and depth_stats[d]['verif'] for d in [0, 1, 2, 3]):
                verif_0 = depth_stats[0]['verif']['mean']
                verif_1 = depth_stats[1]['verif']['mean']
                verif_2 = depth_stats[2]['verif']['mean']
                verif_3 = depth_stats[3]['verif']['mean']
            
                # Check if linear: verif(d) ≈ a * d + b
                # Check if quadratic: verif(d) ≈ a * d² + b
                linear_ratio_1 = (verif_1 - verif_0) / 1 if verif_0 > 0 else 0
                linear_ratio_2 = (verif_2 - verif_0) / 2 if verif_0 > 0 else 0
                linear_ratio_3 = (verif_3 - verif_0) / 3 if verif_0 > 0 else 0
            
                avg_linear_ratio = statistics.mean([r for r in [linear_ratio_1, linear_ratio_2, linear_ratio_3] if r > 0])
                linear_variance = statistics.stdev([linear_ratio_1, linear_ratio_2, linear_ratio_3]) if len([r for r in [linear_ratio_1, linear_ratio_2, linear_ratio_3] if r > 0]) > 1 else 0
            
                print(f"\n  Estimated Complexity:\n")
                print(f"    Linear coefficient (avg): {avg_linear_ratio:.3f}ms per depth level\n")
                print(f"    Linear variance: {linear_variance:.3f}ms (lower = more linear)\n")
                if linear_variance < avg_linear_ratio * 0.3:
                    print(f"    Pattern: Approximately LINEAR O(depth)\n")
                else:
                    print(f"    Pattern: NON-LINEAR (may be quadratic or other)\n")
    
        # ========================================================================
        # 5. SIZE ANALYSIS
        # ========================================================================
        print("\n" + "=" * 80)
        print("## SIZE ANALYSIS\n\n")
        print("---\n\n")
    
        vc_sizes = [m['sizes']['vc_jwt_size_bytes'] for m in metrics 
                    if m['sizes']['vc_jwt_size_bytes'] > 0]
        cvc_sizes = [m['sizes']['cvc_serialized_size_bytes'] for m in metrics 
                     if m['sizes']['cvc_serialized_size_bytes'] > 0]
        vro_sizes = [m['sizes']['vro_jwt_size_bytes'] for m in metrics 
                     if m['sizes']['vro_jwt_size_bytes'] > 0]
        dg_sizes = [m['sizes']['dg_chain_size_bytes'] for m in metrics 
                    if m['sizes']['dg_chain_size_bytes'] > 0]
        req_sizes = [m['sizes']['request_size_bytes'] for m in metrics 
                     if m['sizes']['request_size_bytes'] > 0]
    
        print(f"\nVC-JWT Sizes ({len(vc_sizes)}/{len(metrics)} non-zero):\n")
        if vc_sizes:
            vc_stats = stats_summary(vc_sizes, "VC-JWT")
            print(f"  Mean:     {vc_stats['mean']:.0f} bytes\n")
            print(f"  Median:   {vc_stats['median']:.0f} bytes\n")
            print(f"  Min:      {vc_stats['min']:.0f} bytes\n")
            print(f"  Max:      {vc_stats['max']:.0f} bytes\n")
    
        print(f"\nCVC Serialized Sizes ({len(cvc_sizes)}/{len(metrics)} non-zero):\n")
        if cvc_sizes:
            cvc_stats = stats_summary(cvc_sizes, "CVC")
            print(f"  Mean:     {cvc_stats['mean']:.0f} bytes\n")
            print(f"  Median:   {cvc_stats['median']:.0f} bytes\n")
            print(f"  Min:      {cvc_stats['min']:.0f} bytes\n")
            print(f"  Max:      {cvc_stats['max']:.0f} bytes\n")
            print(f"  Expansion ratio (CVC/VC): {cvc_stats['mean']/vc_stats['mean']:.2f}x\n")
    
        print(f"\nVRO-JWT Sizes ({len(vro_sizes)}/{len(metrics)} non-zero):\n")
        if vro_sizes:
            vro_size_stats = stats_summary(vro_sizes, "VRO")
            print(f"  Mean:     {vro_size_stats['mean']:.0f} bytes\n")
            print(f"  Median:   {vro_size_stats['median']:.0f} bytes\n")
    
        if dg_sizes:
            print(f"\nDG Chain Sizes ({len(dg_sizes)}/{len(metrics)} non-zero):\n")
            dg_stats = stats_summary(dg_sizes, "DG")
            print(f"  Mean:     {dg_stats['mean']:.0f} bytes\n")
            print(f"  Median:   {dg_stats['median']:.0f} bytes\n")
            print(f"  Max:      {dg_stats['max']:.0f} bytes\n")
    
        # ========================================================================
        # 6. INVARIANT ANALYSIS
        # ========================================================================
        print("\n" + "=" * 80)
        print("## INVARIANT ANALYSIS\n\n")
        print("---\n\n")
    
        invariants = [
            'scope_containment_passed',
            'temporal_validity_passed',
            'signature_verification_passed',
            'chain_integrity_passed',
            'structural_validity_passed'
        ]
    
        for inv in invariants:
            passed = sum(1 for m in metrics if m['invariants'][inv])
            print(f"  {inv}: {passed}/{len(metrics)} ({passed/len(metrics)*100:.1f}%)\n")
    
        success_count = sum(1 for m in metrics if m['success'])
        print(f"\n  Overall Success: {success_count}/{len(metrics)} ({success_count/len(metrics)*100:.1f}%)\n")
    
        # ========================================================================
        # 7. BLOCKCHAIN ANCHOR IMPACT ANALYSIS
        # ========================================================================
        print("\n" + "=" * 80)
        print("## BLOCKCHAIN ANCHOR IMPACT ANALYSIS\n\n")
        print("---\n\n")
    
        # Separate requests with and without anchor (only for chain_depth > 0)
        anchor_with = [m for m in metrics if 'ANCHOR' in m.get('scenario', '') and 'NOANCHOR' not in m.get('scenario', '')]
        anchor_without = [m for m in metrics if 'NOANCHOR' in m.get('scenario', '')]
    
        if anchor_with and anchor_without:
            print(f"\nRequests with anchor requirement: {len(anchor_with)}\n")
            print(f"Requests without anchor requirement: {len(anchor_without)}\n")
        
            # Compare latencies
            anchor_with_e2e = [m['e2e_latency']['duration_ms'] for m in anchor_with]
            anchor_without_e2e = [m['e2e_latency']['duration_ms'] for m in anchor_without]
            anchor_with_verif = [m['verification_latency']['duration_ms'] for m in anchor_with 
                                if m['verification_latency']['duration_ms'] > 0]
            anchor_without_verif = [m['verification_latency']['duration_ms'] for m in anchor_without 
                                   if m['verification_latency']['duration_ms'] > 0]
        
            stats_anchor_e2e = stats_summary(anchor_with_e2e, "Anchor-E2E")
            stats_noanchor_e2e = stats_summary(anchor_without_e2e, "NoAnchor-E2E")
            stats_anchor_verif = stats_summary(anchor_with_verif, "Anchor-Verif") if anchor_with_verif else {}
            stats_noanchor_verif = stats_summary(anchor_without_verif, "NoAnchor-Verif") if anchor_without_verif else {}
        
            print(f"\nE2E Latency Comparison:\n")
            print(f"  With anchor:    mean={stats_anchor_e2e['mean']:.3f}ms, median={stats_anchor_e2e['median']:.3f}ms, P95={stats_anchor_e2e['p95']:.3f}ms\n")
            print(f"  Without anchor: mean={stats_noanchor_e2e['mean']:.3f}ms, median={stats_noanchor_e2e['median']:.3f}ms, P95={stats_noanchor_e2e['p95']:.3f}ms\n")
        
            e2e_overhead = stats_anchor_e2e['mean'] - stats_noanchor_e2e['mean']
            e2e_overhead_pct = (e2e_overhead / stats_noanchor_e2e['mean'] * 100) if stats_noanchor_e2e['mean'] > 0 else 0
            print(f"  Anchor overhead: {e2e_overhead:+.3f}ms ({e2e_overhead_pct:+.1f}%)\n")
        
            if stats_anchor_verif and stats_noanchor_verif:
                print(f"\nVerification Latency Comparison:\n")
                print(f"  With anchor:    mean={stats_anchor_verif['mean']:.3f}ms, median={stats_anchor_verif['median']:.3f}ms, P95={stats_anchor_verif['p95']:.3f}ms\n")
                print(f"  Without anchor: mean={stats_noanchor_verif['mean']:.3f}ms, median={stats_noanchor_verif['median']:.3f}ms, P95={stats_noanchor_verif['p95']:.3f}ms\n")
            
                verif_overhead = stats_anchor_verif['mean'] - stats_noanchor_verif['mean']
                verif_overhead_pct = (verif_overhead / stats_noanchor_verif['mean'] * 100) if stats_noanchor_verif['mean'] > 0 else 0
                print(f"  Anchor overhead: {verif_overhead:+.3f}ms ({verif_overhead_pct:+.1f}%)\n")
        
            # Anchor impact by chain depth
            print(f"\nAnchor Impact by Chain Depth:\n")
            for depth in sorted([d for d in depth_stats.keys() if d > 0]):
                anchor_depth_with = [m for m in anchor_with if m.get('chain_depth') == depth]
                anchor_depth_without = [m for m in anchor_without if m.get('chain_depth') == depth]
            
                if anchor_depth_with and anchor_depth_without:
                    with_e2e = statistics.mean([m['e2e_latency']['duration_ms'] for m in anchor_depth_with])
                    without_e2e = statistics.mean([m['e2e_latency']['duration_ms'] for m in anchor_depth_without])
                    overhead = with_e2e - without_e2e
                    overhead_pct = (overhead / without_e2e * 100) if without_e2e > 0 else 0
                    print(f"  Depth {depth}: {overhead:+.3f}ms ({overhead_pct:+.1f}%) overhead\n")
        else:
            print("\n[INFO] Anchor analysis not available (no anchor variable in batch)\n")
    
        # ========================================================================
        # 8. CORRELATIONS AND RELATIONSHIPS
        # ========================================================================
        print("\n" + "=" * 80)
        print("## CORRELATIONS AND RELATIONSHIPS\n\n")
        print("---\n\n")
    
        # Correlation: chain_depth vs latency (already calculated in depth_stats)
        print("\nChain Depth vs Latency (summary):\n")
        for depth in sorted(depth_stats.keys()):
            if depth_stats[depth]['e2e']:
                print(f"  Depth {depth}: E2E mean={depth_stats[depth]['e2e']['mean']:.3f}ms, "
                      f"Verif mean={depth_stats[depth]['verif']['mean']:.3f}ms" if depth_stats[depth]['verif'] else "")
    
        # Correlation: CVC size vs chain depth
        print("\nChain Depth vs CVC Size:\n")
        for depth in sorted(depth_stats.keys()):
            if depth_stats[depth]['cvc_size']:
                print(f"  Depth {depth}: CVC mean={depth_stats[depth]['cvc_size']['mean']:.0f} bytes\n")
    
        # Correlation: CVC size vs verification latency
        print("\nCVC Size vs Verification Latency:\n")
        cvc_verif_pairs = [(m['sizes']['cvc_serialized_size_bytes'], m['verification_latency']['duration_ms']) 
                           for m in metrics 
                           if m['sizes']['cvc_serialized_size_bytes'] > 0 and m['verification_latency']['duration_ms'] > 0]
        if cvc_verif_pairs:
            cvc_sizes_list = [p[0] for p in cvc_verif_pairs]
            verif_times_list = [p[1] for p in cvc_verif_pairs]
            # Simple correlation: mean verification time per CVC size range
            size_ranges = [(0, 2000), (2000, 4000), (4000, 6000), (6000, 8000), (8000, 10000)]
            print("  CVC Size Range -> Mean Verification Time:\n")
            for min_size, max_size in size_ranges:
                range_pairs = [(c, v) for c, v in cvc_verif_pairs if min_size <= c < max_size]
                if range_pairs:
                    mean_verif = statistics.mean([v for _, v in range_pairs])
                    print(f"    {min_size}-{max_size} bytes: {mean_verif:.3f}ms ({len(range_pairs)} requests)\n")
    
        # ========================================================================
        # 9. DETERMINISM VERIFICATION
        # ========================================================================
        print("\n" + "=" * 80)
        print("## DETERMINISM VERIFICATION\n\n")
        print("---\n\n")
    
        # Check VRO hash uniqueness
        vro_hashes = [m.get('vro_hash') for m in metrics if m.get('vro_hash')]
        unique_hashes = len(set(vro_hashes))
        total_hashes = len(vro_hashes)
    
        print(f"\nVRO Hash Analysis:\n")
        print(f"  Total VRO hashes: {total_hashes}\n")
        print(f"  Unique VRO hashes: {unique_hashes}\n")
        print(f"  Uniqueness rate: {unique_hashes/total_hashes*100:.1f}%\n")
    
        if unique_hashes == total_hashes:
            print(f"  [OK] All VRO hashes are unique (deterministic outputs)\n")
        else:
            duplicates = total_hashes - unique_hashes
            print(f"  [WARNING] {duplicates} duplicate VRO hashes found (non-deterministic)\n")
    
        # Check chain fingerprints
        chain_fingerprints = [m.get('chain_fingerprint') for m in metrics if m.get('chain_fingerprint')]
        unique_fingerprints = len(set(chain_fingerprints)) if chain_fingerprints else 0
        total_fingerprints = len(chain_fingerprints)
    
        if total_fingerprints > 0:
            print(f"\nChain Fingerprint Analysis:\n")
            print(f"  Total fingerprints: {total_fingerprints}\n")
            print(f"  Unique fingerprints: {unique_fingerprints}\n")
            print(f"  Uniqueness rate: {unique_fingerprints/total_fingerprints*100:.1f}%\n")
    
        # ========================================================================
        # 10. OUTLIER ANALYSIS
        # ========================================================================
        print("\n" + "=" * 80)
        print("## OUTLIER ANALYSIS\n\n")
        print("---\n\n")
    
        # Outliers using IQR method
        q1 = e2e_stats['p25']
        q3 = e2e_stats['p75']
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
    
        outliers = [m for m in metrics 
                    if m['e2e_latency']['duration_ms'] < lower_bound or 
                       m['e2e_latency']['duration_ms'] > upper_bound]
    
        print(f"\nE2E Latency Outliers (IQR method): {len(outliers)}/{len(metrics)} ({len(outliers)/len(metrics)*100:.1f}%)\n")
        if outliers:
            outlier_e2e = [m['e2e_latency']['duration_ms'] for m in outliers]
            print(f"  Outlier range: {min(outlier_e2e):.3f}ms - {max(outlier_e2e):.3f}ms\n")
            print(f"  Normal range: {lower_bound:.3f}ms - {upper_bound:.3f}ms\n")
    
        # ========================================================================
        # 11. EXECUTIVE SUMMARY
        # ========================================================================
        print("\n" + "=" * 80)
        print("## EXECUTIVE SUMMARY\n\n")
        print("---\n\n")
    
        print(f"\n[OK] Total Requests: {len(metrics)}\n")
        print(f"[OK] Success Rate: {success_count/len(metrics)*100:.1f}%\n")
        print(f"[OK] Average E2E Latency: {e2e_stats['mean']:.2f}ms (median: {e2e_stats['median']:.2f}ms)\n")
        print(f"[OK] P95 E2E Latency: {e2e_stats['p95']:.2f}ms\n")
        print(f"[OK] Average Normalization: {norm_stats['mean']:.2f}ms\n")
        print(f"[OK] Average Verification: {verif_stats['mean']:.2f}ms\n")
        print(f"[OK] Average CVC Size: {cvc_stats['mean']:.0f} bytes\n")
        print(f"[OK] CVC Expansion: {cvc_stats['mean']/vc_stats['mean']:.2f}x original VC size\n")
    
        # Key findings
        print(f"\nKey Findings:\n")
    
        # Format Independence
        if 'VC-JWT' in profile_stats and 'VC-LD' in profile_stats:
            if profile_stats['VC-JWT']['norm'] and profile_stats['VC-LD']['norm']:
                norm_diff_pct = abs(profile_stats['VC-JWT']['norm']['mean'] - profile_stats['VC-LD']['norm']['mean']) / min(profile_stats['VC-JWT']['norm']['mean'], profile_stats['VC-LD']['norm']['mean']) * 100
                print(f"  Format Independence: Normalization difference {norm_diff_pct:.1f}% (lower = more independent)\n")
    
        # Scalability
        if 0 in depth_stats and 3 in depth_stats:
            if depth_stats[0]['verif'] and depth_stats[3]['verif']:
                scalability_ratio = depth_stats[3]['verif']['mean'] / depth_stats[0]['verif']['mean'] if depth_stats[0]['verif']['mean'] > 0 else 0
                print(f"  Scalability: Depth 3 is {scalability_ratio:.2f}x slower than depth 0\n")
    
        # Anchor Impact
        if anchor_with and anchor_without:
            anchor_overhead_pct = e2e_overhead_pct
            print(f"  Anchor Overhead: {anchor_overhead_pct:+.1f}% on E2E latency\n")
    
        # Overhead
        if overheads:
            overhead_pct = overhead_stats['mean']/e2e_stats['mean']*100
            print(f"  System Overhead: {overhead_pct:.1f}% of E2E latency\n")
    
        print("\n---\n\n")
        print("## 11. Executive Summary\n\n")
    
        print(f"- **Total Requests:** {len(metrics)}\n")
        print(f"- **Success Rate:** {success_count/len(metrics)*100:.1f}%\n")
        print(f"- **Average E2E Latency:** {e2e_stats['mean']:.2f}ms (median: {e2e_stats['median']:.2f}ms)\n")
        print(f"- **P95 E2E Latency:** {e2e_stats['p95']:.2f}ms\n")
        print(f"- **Average Normalization:** {norm_stats['mean']:.2f}ms\n")
        print(f"- **Average Verification:** {verif_stats['mean']:.2f}ms\n")
        print(f"- **Average CVC Size:** {cvc_stats['mean']:.0f} bytes\n")
        print(f"- **CVC Expansion:** {cvc_stats['mean']/vc_stats['mean']:.2f}x original VC size\n\n")
    
        # Key findings
        print("### Key Findings\n\n")
    
        # Format Independence
        if 'VC-JWT' in profile_stats and 'VC-LD' in profile_stats:
            if profile_stats['VC-JWT']['norm'] and profile_stats['VC-LD']['norm']:
                norm_diff_pct = abs(profile_stats['VC-JWT']['norm']['mean'] - profile_stats['VC-LD']['norm']['mean']) / min(profile_stats['VC-JWT']['norm']['mean'], profile_stats['VC-LD']['norm']['mean']) * 100
                print(f"- **Format Independence:** Normalization difference {norm_diff_pct:.1f}% (lower = more independent)\n")
    
        # Scalability
        if 0 in depth_stats and 3 in depth_stats:
            if depth_stats[0]['verif'] and depth_stats[3]['verif']:
                scalability_ratio = depth_stats[3]['verif']['mean'] / depth_stats[0]['verif']['mean'] if depth_stats[0]['verif']['mean'] > 0 else 0
                print(f"- **Scalability:** Depth 3 is {scalability_ratio:.2f}x slower than depth 0\n")
    
        # Anchor Impact
        if anchor_with and anchor_without:
            anchor_overhead_pct = e2e_overhead_pct
            print(f"- **Anchor Overhead:** {anchor_overhead_pct:+.1f}% on E2E latency\n")
    
        # Overhead
        if overheads:
            overhead_pct = overhead_stats['mean']/e2e_stats['mean']*100
            print(f"- **System Overhead:** {overhead_pct:.1f}% of E2E latency\n")
    
    finally:
        # Restore stdout and close file
        sys.stdout = tee.stdout
        tee.close()
        print(f"\n[OK] Analysis report saved to: {output_file}")

if __name__ == "__main__":
    analyze_metrics()