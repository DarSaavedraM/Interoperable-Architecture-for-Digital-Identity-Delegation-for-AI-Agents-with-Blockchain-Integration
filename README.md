# Interoperable Architecture for Digital Identity Delegation for AI Agents with Blockchain Integration

A research implementation of an interoperable architecture for verifiable delegation of digital identity for artificial intelligence agents.

## Overview

This repository contains a deterministic, minimal working prototype that validates the proposed architecture for verifiable delegation of digital identity. The implementation demonstrates:

- **Trust Gateway (TG)**: Protocol-agnostic API for request normalization and routing
- **Canonical Verification Context (CVC)**: Standardized context that normalizes different credential encodings and transport protocols
- **Verification Engine (VE)**: Core logic for deterministic verification, independent of original format
- **Delegation Grants (DG)**: SD-JWT based delegation chains
- **Policy Engine**: Logic for evaluating verification policies and revocation status

**Key Architectural Principle**: Once the Trust Gateway (L3) has normalized any incoming request into a Canonical Verification Context (CVC), the system performs verification deterministically, independent of the transport protocol (OIDC4VP, DIDComm, HTTPS) or credential encoding (VC-LD, VC-JWT, SD-JWT).

## Features

- ✅ Fully offline operation for reproducibility
- ✅ Open cryptography standards (Ed25519, JWS, JWT, StatusList2021)
- ✅ Protocol-agnostic normalization to CVC
- ✅ Support for multiple credential encodings (VC-JWT, VC-LD normalization)
- ✅ VC-JWT credential verification (fully implemented)
- ✅ VC-LD credential normalization (demonstrates format independence)
- ✅ DG-SD-JWT delegation chains
- ✅ StatusList2021 revocation verification
- ✅ Signed verification results (VRO JWT)
- ✅ Deterministic and reproducible outputs

## Requirements

- Python 3.10+
- See `requirements.txt` for Python dependencies

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Initialize Fixtures

Generate all necessary keys, credentials, and test data:

```bash
python scripts/init_fixtures.py
```

This generates:
- Ed25519 key pairs for all actors
- JWKS files
- Example VC-JWT credentials
- DG-SD-JWT delegation chains
- Ready-to-use request files

### 2. Start Server

```bash
uvicorn gateway.main:app --host 0.0.0.0 --port 8443
```

### 3. Test Verification

**Using Python test script:**
```bash
# Run all scenarios including blockchain
python scripts/tests/test_all_scenarios.py --include-blockchain

# Run individual scenarios
python scripts/tests/test_s1_federated.py
python scripts/tests/test_s2_ssi.py
# ... etc
```

**Using curl:**
```bash
curl -s -X POST http://localhost:8443/verify \
  -H "Content-Type: application/json" \
  -d @fixtures/requests/req_vc_jwt_only.json | jq .
```

**Using PowerShell (Windows):**
```powershell
$body = Get-Content fixtures/requests/req_vc_jwt_only.json -Raw
Invoke-RestMethod -Uri http://localhost:8443/verify -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 10
```

**With delegation chain:**
```bash
curl -s -X POST http://localhost:8443/verify \
  -H "Content-Type: application/json" \
  -d @fixtures/requests/req_vc_jwt_plus_dg_chain.json | jq .
```

## Test Scenarios

The prototype implements five main test scenarios:

- **S1**: Federated flow (VC-JWT + SD-JWT with DG; OIDC4VP presentation)
- **S2**: SSI flow (VC-LD(BBS+) with StatusList2021 + DG-LD or DG-SD-JWT)
- **S3**: Hybrid agent delegation (human→agent DG; constrained scope; revocation freshness)
- **S4**: Negative cases (expired DG, revoked status, scope escalation, key-binding mismatch)
- **S5**: Blockchain anchor (delegation chain anchoring with and without anchor requirement)

### Individual Tests

Each scenario can be tested individually:

```bash
# Test individual scenarios
python scripts/tests/test_s1_federated.py
python scripts/tests/test_s2_ssi.py
python scripts/tests/test_s3_hybrid.py
python scripts/tests/test_s4_negative.py
python scripts/tests/test_s5_blockchain.py
```

### Conjoint Tests

Run all scenarios together:

```bash
# Run all scenarios (S1-S4, without blockchain)
python scripts/tests/test_all_scenarios.py

# Run all scenarios including blockchain (S1-S5)
python scripts/tests/test_all_scenarios.py --include-blockchain

# Run specific scenarios
python scripts/tests/test_all_scenarios.py --scenarios S1,S2,S5
```

**Test Results**: ✅ All scenarios passing (S1-S5)

## Project Structure

```
.
├── gateway/          # FastAPI API and normalization
│   ├── main.py      # API endpoints
│   ├── adapters.py  # Profile detection and normalization
│   ├── policy.py    # Policy loading
│   ├── schemas.py   # Pydantic models
│   └── config.py    # Configuration
├── verifier/         # Core verification logic
│   ├── verifier.py  # Main verification engine
│   ├── crypto.py    # Cryptographic utilities
│   ├── status.py    # Status verification
│   └── constants.py # Error codes and constants
├── fixtures/         # Test data and credentials
│   ├── keys/        # Cryptographic keys
│   ├── requests/    # Example verification requests
│   └── status/      # StatusList2021 documents
├── scripts/          # Generation and test scripts
│   ├── tests/       # Individual and conjoint test scenarios
│   │   ├── base.py              # Base test utilities
│   │   ├── test_s1_federated.py # S1: Federated flow
│   │   ├── test_s2_ssi.py       # S2: SSI flow
│   │   ├── test_s3_hybrid.py    # S3: Hybrid agent
│   │   ├── test_s4_negative.py  # S4: Negative cases
│   │   ├── test_s5_blockchain.py # S5: Blockchain anchor
│   │   └── test_all_scenarios.py # All scenarios (conjoint)
│   └── batch/       # Batch generation and metrics
│       ├── config.py            # Batch configuration
│       ├── generate_batch.py    # Generate with anchor variable
│       └── run_batch_metrics.py # Collect metrics with anchor
└── requirements.txt # Python dependencies
```

## API Endpoints

### `POST /verify`

Verifies a credential presentation and optional delegation chain.

**Request:**
```json
{
  "presentation": {
    "type": "VC-JWT",
    "jwt": "<jwt_token>"
  },
  "policy_id": "P-001",
  "delegation_chain": ["<dg1_jwt>", "<dg2_jwt>"],
  "holder_binding": {"type": "JWS", "proof": "demo-nonce-signature"}
}
```

**Response:**
```json
{
  "vro_jwt": "<signed_jwt>",
  "metrics": {...}
}
```

### `POST /verify/oidc4vp`

OIDC4VP verification endpoint. Receives OIDC4VP authorization response with `vp_token`, extracts Verifiable Presentation, and normalizes to CVC.

**Note:** Full OIDC4VP flow (authorization request/response) is not implemented, but the normalization demonstrates protocol independence.

### `GET /health`

Health check endpoint.

## Metrics Collection

The project includes a metrics framework for research evaluation. All metrics are based on actual measurements from system execution.

### Batch Metrics with Blockchain Variable

**Generate batch requests (with blockchain anchor as variable):**
```bash
# Generate batch with anchor variable (default: includes anchor)
python scripts/batch/generate_batch.py

# Generate batch without anchor variable
python scripts/batch/generate_batch.py --no-anchor

# Custom number of requests and seed
python scripts/batch/generate_batch.py --num-requests 500 --seed 42
```

**Collect metrics from batch (requires server running):**
```bash
# Collect metrics (automatically saves as _with_anchor or _no_anchor based on batch)
python scripts/batch/run_batch_metrics.py
```

**Analyze collected metrics:**
```bash
# Generate detailed analysis report (saves to metrics/reports/)
python scripts/analyze_metrics_detailed.py
```

The analysis report is automatically saved to `metrics/reports/metrics_analysis_YYYYMMDD_HHMMSS.md` and also printed to console.

## Known Limitations

1. **VC-LD Full Verification**: VC-LD normalization to CVC works, but full BBS+ signature verification requires external libraries (SSI/DIDKit).

2. **OIDC4VP Full Flow**: OIDC4VP `vp_token` normalization works, but the complete OIDC4VP authorization flow (request/response) is not implemented.

3. **Key Binding PoP**: Key binding field is detected and validated, but full proof-of-possession (PoP) verification requires challenge-response mechanisms (DPoP, mTLS).

4. **StatusList2021**: Status document fetching and parsing works, but full bitstring decoding is simplified for prototype purposes.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture and implementation documentation
- [scripts/TESTING.md](scripts/TESTING.md) - Comprehensive testing guide and structure

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

If you use this software in your research, please cite it. See [CITATION.cff](CITATION.cff) for citation information.
