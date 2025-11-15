# Testing Guide

This document describes the testing structure and how to run different types of tests.

## Test Structure

The testing framework is organized into three categories:

1. **Individual Tests**: Each scenario can be tested independently
2. **Conjoint Tests**: All scenarios tested together with configurable options
3. **Batch Metrics**: Statistical analysis with blockchain anchor as a variable

## 1. Individual Tests

Each test scenario has its own script in `scripts/tests/`:

### S1: Federated Flow
```bash
python scripts/tests/test_s1_federated.py
```
Tests VC-JWT with delegation chain and OIDC4VP normalization.

### S2: SSI Flow
```bash
python scripts/tests/test_s2_ssi.py
```
Tests VC-LD normalization to CVC and format independence.

### S3: Hybrid Agent Delegation
```bash
python scripts/tests/test_s3_hybrid.py
```
Tests human→agent delegation with scope containment and revocation checks.

### S4: Negative Cases
```bash
python scripts/tests/test_s4_negative.py
```
Tests that negative cases (expired, revoked, scope escalation) are properly rejected.

### S5: Blockchain Anchor
```bash
python scripts/tests/test_s5_blockchain.py
```
Tests delegation chain anchoring with and without anchor requirement.

## 2. Conjoint Tests

Run all scenarios together with flexible configuration:

### All Scenarios (S1-S4, default)
```bash
python scripts/tests/test_all_scenarios.py
```

### All Scenarios Including Blockchain (S1-S5)
```bash
python scripts/tests/test_all_scenarios.py --include-blockchain
```

### Specific Scenarios Only
```bash
# Run only S1, S2, and S5
python scripts/tests/test_all_scenarios.py --scenarios S1,S2,S5
```

## 3. Batch Metrics with Blockchain Variable

### Generate Batch Requests

Generate a batch of requests with blockchain anchor as a configurable variable:

```bash
# Generate 1000 requests with anchor variable (default)
python scripts/batch/generate_batch.py

# Generate without anchor variable
python scripts/batch/generate_batch.py --no-anchor

# Custom configuration
python scripts/batch/generate_batch.py --num-requests 500 --seed 42
```

**Configuration** (in `scripts/batch/config.py`):
- Profile distribution: 70% VC-JWT, 30% VC-LD
- Chain depth distribution: 40% depth 0, 30% depth 1, 20% depth 2, 10% depth 3
- Anchor distribution: 50% with anchor, 50% without anchor (for requests with chain)

### Collect Metrics

Run metrics collection on the generated batch:

```bash
# Ensure server is running first
python scripts/start_server.py

# In another terminal, collect metrics
python scripts/batch/run_batch_metrics.py
```

The script will:
- Process all batch requests
- Collect comprehensive metrics including anchor metrics
- Save results to `metrics/collected_metrics_batch.json`
- Generate summary in `metrics/batch_results.json`

### Analyze Metrics

Analyze the collected metrics:

```bash
# Analyze individual batch metrics
python scripts/analyze_metrics_detailed.py

# Compare batches with and without anchor
# Analysis report is automatically generated and saved to metrics/reports/
```

This generates detailed statistical analysis including:
- Latency breakdown by profile and chain depth
- Anchor impact analysis (if anchor variable was included)
- Size metrics and invariant pass rates
- Performance comparisons
- Direct comparison between batches with/without anchor

## Test Organization Benefits

### Modularity
- Each test is independent and can be run in isolation
- Easy to add new test scenarios
- Clear separation of concerns

### Flexibility
- Run individual tests for debugging
- Run conjoint tests for comprehensive validation
- Configure batch tests for different research questions

### Documentation
- Each test file documents its specific scenario
- Clear test structure for academic presentation
- Easy to understand test coverage

## Legacy Tests

**Note**: All testing is now done through the modular test structure described above. The old test scripts have been removed in favor of the cleaner, more maintainable structure.

## Requirements

All tests require:
1. Server running: `python scripts/start_server.py`
2. Fixtures initialized: `python scripts/init_fixtures.py`

## Troubleshooting

### Import Errors
If you get import errors, ensure you're running from the project root:
```bash
cd /path/to/project
python scripts/tests/test_s1_federated.py
```

### Server Not Running
All tests require the server to be running:
```bash
python scripts/start_server.py
```

### Missing Fixtures
Initialize fixtures if tests fail with file not found errors:
```bash
python scripts/init_fixtures.py
```

