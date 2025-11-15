# Architecture Documentation

## Overview

This prototype implements a digital credential verification architecture with delegation support, following the principles described in the research. The architecture demonstrates format-independence and protocol-agnostic verification through the Canonical Verification Context (CVC) abstraction.

## Core Components

### 1. Trust Gateway (TG) - `gateway/`

**Responsibility:** Presentation normalization and CVC construction

- **`main.py`**: FastAPI API with verification endpoints
- **`adapters.py`**: Adapters for normalizing different presentation formats (VC-JWT, VC-LD)
- **`policy.py`**: Verification policy loading and management
- **`schemas.py`**: Pydantic models for validation
- **`config.py`**: Centralized configuration

**Flow:**
1. Receives `VerificationRequest` with credential presentation (VC-JWT, VC-LD, etc.)
2. Detects profile (format-agnostic detection)
3. Normalizes to CVC format (protocol and format independent)
4. Sends CVC to Verification Engine
5. Returns signed VRO

**Key Principle**: Once normalized to CVC, verification is deterministic and independent of:
- Transport protocol (OIDC4VP, DIDComm, HTTPS)
- Credential encoding (VC-JWT, VC-LD, SD-JWT)

### 2. Verification Engine (VE) - `verifier/`

**Responsibility:** Cryptographic verification and business logic

- **`verifier.py`**: Main verification engine
- **`crypto.py`**: Cryptographic utilities (JWT/JWS, JWKS)
- **`status.py`**: StatusList2021 status verification
- **`anchor.py`**: Blockchain anchor abstraction (mock implementation)
- **`constants.py`**: Constants and error codes

**Verification Flow:**
1. Structural validation of CVC
2. Credential verification (format-agnostic, based on CVC structure):
   - VC-JWT: Full cryptographic verification (signature, temporality, status)
   - VC-LD: Normalization demonstrated (full verification requires LD-Proof libraries)
3. Delegation chain verification (if present):
   - Signature, scope containment, temporal, status verification
   - Blockchain anchor verification/anchoring (if `require_anchor: true`)
4. Policy evaluation
5. Deterministic VRO generation
6. VRO signing

**Key Principle**: Verification operates on the normalized CVC structure, making it independent of the original credential format or transport protocol.

### 3. Canonical Verification Context (CVC)

Standardized structure that normalizes different formats:

```python
{
    "I_issuer": str,      # Issuer identifier
    "I_subject": str,     # Subject identifier
    "C": [...],           # Normalized claims
    "pi": [...],          # Proof descriptors
    "Delta": [...],       # Parsed delegations
    "P": {...},           # Loaded policy
    "S": {...},           # Status references
    "M": {...}            # Metadata
}
```

### 4. Delegation Grants (DG)

Delegation chains enabling authorization transfer:
- Signature verification
- Temporal validation
- Status verification
- Scope containment (child scope must be subset of parent)
- Key binding validation (basic PoP)
- Blockchain anchor verification/anchoring (when `require_anchor: true`)

## Verification Flow

```
Request → Gateway → Normalization → CVC → Verifier → VRO
```

1. **Request**: Client sends `VerificationRequest` with VC-JWT and optionally DG chain
2. **Gateway**: Detects profile, normalizes, builds CVC
3. **Verifier**: Cryptographically verifies and applies policies
4. **VRO**: Generates and signs Verification Result Object
5. **Response**: Returns VRO JWT to client

## Error Codes

The system uses standardized error codes following the conceptual model taxonomy:

- `OK`: Successful verification
- `100` (FormatError): Malformed or unrecognized input
- `E200` (ProofError): Invalid or unverifiable cryptographic proof
- `E300` (ChainError): Incomplete or cyclic delegation chain
- `E400` (ScopeViolation): Operation exceeds delegated authority
- `E500` (PolicyError): Failed policy or issuer validation
- `E900` (InternalError): Gateway failure or processing exception

## Security Properties

- All cryptographic operations use Ed25519 (EdDSA)
- Signature verification at all levels
- Temporality validation with clock skew
- Revocation status verification (StatusList2021)
- Scope containment in delegation chains
- Key binding validation (basic PoP)
- Holder binding structure validation
- Blockchain anchor for delegation chain integrity (when enabled)
- Signed VRO for authenticity guarantee
- Fail-closed operation (configurable via policy)

## Determinism

For reproducibility in tests:
- Fixed timestamp in VRO (`DETERMINISTIC_TIMESTAMP`)
- Chain fingerprint using SHA256
- No external network dependencies
- Deterministic JSON serialization (sorted keys)

## Known Limitations

1. **VC-LD Full Verification**: VC-LD normalization to CVC works, but full BBS+ signature verification requires external libraries (SSI/DIDKit).

2. **OIDC4VP Full Flow**: OIDC4VP `vp_token` normalization works, but the complete OIDC4VP authorization flow (request/response) is not implemented.

3. **Key Binding PoP**: Key binding field is validated (kid existence in JWKS), but full proof-of-possession (PoP) verification requires challenge-response mechanisms (DPoP, mTLS). In production, delegate JWKS would be resolved from DID document or registry.

4. **StatusList2021**: Status document fetching and parsing works, but full bitstring decoding is simplified for prototype purposes.

5. **Holder Binding**: Holder binding structure is validated, but full cryptographic verification of the proof signature requires the holder's public key.

6. **Blockchain Anchor**: Mock implementation uses JSON storage for prototype purposes. In production, this would connect to a real blockchain (Ethereum, Hyperledger, etc.) for immutable anchor storage.

## Metrics Framework

The system includes a metrics framework for research evaluation:

- **Performance Metrics**: End-to-end latency, normalization overhead, verification time
- **Correctness Metrics**: Invariant verification rates (scope containment, temporal validity, etc.)
- **Format Independence Metrics**: Normalization time comparison between VC-JWT and VC-LD
- **Delegation Metrics**: Chain depth distribution, scope reduction, scalability analysis
- **Security Metrics**: Error code distribution, determinism verification, policy enforcement

All metrics are measured from this implementation only. No external system comparisons are included.
