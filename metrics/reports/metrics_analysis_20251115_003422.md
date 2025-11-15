# Detailed Verification Metrics Analysis

**Generated:** 2025-11-15 00:34:22

**Total Requests:** 1200

**Metrics Source:** metrics\collected_metrics_batch_with_anchor.json


---


## 1. Latency Statistics (End-to-End)


- **Count:** 1200

- **Mean:** 58.604 ms

- **Median:** 34.468 ms

- **Std Dev:** 75.498 ms

- **Min:** 4.593 ms

- **Max:** 710.424 ms

- **P25:** 16.948 ms

- **P75:** 65.102 ms

- **P90:** 137.938 ms

- **P95:** 196.725 ms

- **P99:** 390.174 ms



================================================================================
## LATENCY COMPONENT ANALYSIS


---



Normalization Latency (1200/1200 non-zero):

  Mean:     2.678 ms

  Median:   1.222 ms

  Std Dev:  4.711 ms

  Min:      0.260 ms

  Max:      72.992 ms

  P95:      9.797 ms


Verification Latency (1200/1200 non-zero):

  Mean:     28.979 ms

  Median:   13.687 ms

  Std Dev:  48.079 ms

  Min:      0.801 ms

  Max:      666.038 ms

  P95:      109.893 ms


VRO Signing Latency (1200/1200 non-zero):

  Mean:     3.209 ms

  Median:   1.647 ms

  P95:      7.951 ms


Status Fetch Latency (1052/1200 non-zero):

  Mean:     1.549 ms

  Median:   0.868 ms

  P95:      4.925 ms


Overhead Analysis:

  Mean overhead (E2E - components): 22.381 ms

  Median overhead: 10.950 ms

  Overhead % of E2E: 38.2%


================================================================================
## FORMAT INDEPENDENCE ANALYSIS (VC-JWT vs VC-LD)


---



VC-JWT (565 requests, 47.1%):

  E2E:      mean=61.989ms, median=36.510ms, P95=193.951ms

  Norm:     mean=2.736ms, median=1.325ms, P95=10.098ms

  Verif:    mean=32.858ms, median=16.206ms, P95=122.556ms

  CVC Size: mean=5307 bytes, median=4107 bytes


VC-LD (635 requests, 52.9%):

  E2E:      mean=55.592ms, median=31.730ms, P95=197.435ms

  Norm:     mean=2.626ms, median=1.107ms, P95=9.049ms

  Verif:    mean=25.528ms, median=11.208ms, P95=93.098ms

  CVC Size: mean=5562 bytes, median=4388 bytes


Format Independence Comparison:

  E2E Latency Difference: 6.397ms (11.5% of smaller value)

  Normalization Latency Difference: 0.109ms (4.2% of smaller value)

  Verification Latency Difference: 7.331ms (28.7% of smaller value)

  Normalization Independence Index: 0.971 (1.0 = perfect independence)


================================================================================
## SCALABILITY ANALYSIS (Chain Depth Impact)


---



Chain Depth 0 (286 requests, 23.8%):

  E2E:      mean=36.595ms, median=21.708ms, P95=131.354ms

  Norm:     mean=2.280ms, median=1.003ms

  Verif:    mean=7.154ms, median=3.930ms, P95=29.060ms

  CVC Size: mean=1665 bytes, median=1822 bytes


Chain Depth 1 (323 requests, 26.9%):

  E2E:      mean=47.087ms, median=29.564ms, P95=163.927ms

  Norm:     mean=2.863ms, median=1.260ms

  Verif:    mean=17.534ms, median=10.230ms, P95=44.155ms

  CVC Size: mean=4235 bytes, median=4381 bytes


Chain Depth 2 (312 requests, 26.0%):

  E2E:      mean=73.030ms, median=40.227ms, P95=230.919ms

  Norm:     mean=2.862ms, median=1.191ms

  Verif:    mean=40.891ms, median=21.303ms, P95=134.287ms

  CVC Size: mean=6753 bytes, median=6886 bytes


Chain Depth 3 (279 requests, 23.2%):

  E2E:      mean=78.367ms, median=49.629ms, P95=222.625ms

  Norm:     mean=2.665ms, median=1.434ms

  Verif:    mean=51.282ms, median=30.229ms, P95=158.396ms

  CVC Size: mean=9245 bytes, median=9171 bytes


Scalability Metrics (relative to depth=0):

  Depth 1: 17.534ms (2.45x depth=0)

  Depth 2: 40.891ms (5.72x depth=0)

  Depth 3: 51.282ms (7.17x depth=0)


  Estimated Complexity:

    Linear coefficient (avg): 13.986ms per depth level

    Linear variance: 3.304ms (lower = more linear)

    Pattern: Approximately LINEAR O(depth)


================================================================================
## SIZE ANALYSIS


---



VC-JWT Sizes (565/1200 non-zero):

  Mean:     644 bytes

  Median:   638 bytes

  Min:      638 bytes

  Max:      673 bytes


CVC Serialized Sizes (1200/1200 non-zero):

  Mean:     5442 bytes

  Median:   4388 bytes

  Min:      1480 bytes

  Max:      9452 bytes

  Expansion ratio (CVC/VC): 8.44x


VRO-JWT Sizes (1200/1200 non-zero):

  Mean:     525 bytes

  Median:   543 bytes


DG Chain Sizes (914/1200 non-zero):

  Mean:     2837 bytes

  Median:   2904 bytes

  Max:      4365 bytes


================================================================================
## INVARIANT ANALYSIS


---


  scope_containment_passed: 1200/1200 (100.0%)

  temporal_validity_passed: 1200/1200 (100.0%)

  signature_verification_passed: 1200/1200 (100.0%)

  chain_integrity_passed: 1200/1200 (100.0%)

  structural_validity_passed: 1200/1200 (100.0%)


  Overall Success: 1200/1200 (100.0%)


================================================================================
## BLOCKCHAIN ANCHOR IMPACT ANALYSIS


---



Requests with anchor requirement: 455

Requests without anchor requirement: 459


E2E Latency Comparison:

  With anchor:    mean=77.788ms, median=44.178ms, P95=242.782ms

  Without anchor: mean=53.301ms, median=33.576ms, P95=165.056ms

  Anchor overhead: +24.487ms (+45.9%)


Verification Latency Comparison:

  With anchor:    mean=49.740ms, median=26.933ms, P95=167.497ms

  Without anchor: mean=21.998ms, median=13.317ms, P95=67.305ms

  Anchor overhead: +27.742ms (+126.1%)


Anchor Impact by Chain Depth:

  Depth 1: +5.541ms (+12.5%) overhead

  Depth 2: +31.401ms (+55.0%) overhead

  Depth 3: +37.649ms (+63.2%) overhead


================================================================================
## CORRELATIONS AND RELATIONSHIPS


---



Chain Depth vs Latency (summary):

  Depth 0: E2E mean=36.595ms, Verif mean=7.154ms
  Depth 1: E2E mean=47.087ms, Verif mean=17.534ms
  Depth 2: E2E mean=73.030ms, Verif mean=40.891ms
  Depth 3: E2E mean=78.367ms, Verif mean=51.282ms

Chain Depth vs CVC Size:

  Depth 0: CVC mean=1665 bytes

  Depth 1: CVC mean=4235 bytes

  Depth 2: CVC mean=6753 bytes

  Depth 3: CVC mean=9245 bytes


CVC Size vs Verification Latency:

  CVC Size Range -> Mean Verification Time:

    0-2000 bytes: 7.154ms (286 requests)

    4000-6000 bytes: 17.534ms (323 requests)

    6000-8000 bytes: 40.891ms (312 requests)

    8000-10000 bytes: 51.282ms (279 requests)


================================================================================
## DETERMINISM VERIFICATION


---



VRO Hash Analysis:

  Total VRO hashes: 1200

  Unique VRO hashes: 1200

  Uniqueness rate: 100.0%

  [OK] All VRO hashes are unique (deterministic outputs)


================================================================================
## OUTLIER ANALYSIS


---



E2E Latency Outliers (IQR method): 121/1200 (10.1%)

  Outlier range: 137.839ms - 710.424ms

  Normal range: -55.284ms - 137.333ms


================================================================================
## EXECUTIVE SUMMARY


---



[OK] Total Requests: 1200

[OK] Success Rate: 100.0%

[OK] Average E2E Latency: 58.60ms (median: 34.47ms)

[OK] P95 E2E Latency: 196.72ms

[OK] Average Normalization: 2.68ms

[OK] Average Verification: 28.98ms

[OK] Average CVC Size: 5442 bytes

[OK] CVC Expansion: 8.44x original VC size


Key Findings:

  Format Independence: Normalization difference 4.2% (lower = more independent)

  Scalability: Depth 3 is 7.17x slower than depth 0

  Anchor Overhead: +45.9% on E2E latency

  System Overhead: 38.2% of E2E latency


---


## 11. Executive Summary


- **Total Requests:** 1200

- **Success Rate:** 100.0%

- **Average E2E Latency:** 58.60ms (median: 34.47ms)

- **P95 E2E Latency:** 196.72ms

- **Average Normalization:** 2.68ms

- **Average Verification:** 28.98ms

- **Average CVC Size:** 5442 bytes

- **CVC Expansion:** 8.44x original VC size


### Key Findings


- **Format Independence:** Normalization difference 4.2% (lower = more independent)

- **Scalability:** Depth 3 is 7.17x slower than depth 0

- **Anchor Overhead:** +45.9% on E2E latency

- **System Overhead:** 38.2% of E2E latency

