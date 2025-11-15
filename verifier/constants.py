"""
Constants for error codes and configuration values.

Error taxonomy follows the conceptual model:
- 100: FormatError - Malformed or unrecognized input
- E200: ProofError - Invalid or unverifiable cryptographic proof
- E300: ChainError - Incomplete or cyclic delegation chain
- E400: ScopeViolation - Operation exceeds delegated authority
- E500: PolicyError - Failed policy or issuer validation
- E900: InternalError - Gateway failure or processing exception
"""

# Verification error codes
class ErrorCode:
    """Verification system error codes following conceptual model taxonomy."""
    
    # Success
    OK = "OK"
    
    # 100: FormatError - Malformed or unrecognized input
    FORMAT_ERROR = "100"
    STRUCT = "100"  # Structural errors (malformed CVC, missing fields)
    
    # E200: ProofError - Invalid or unverifiable cryptographic proof
    PROOF_ERROR = "E200"
    ALG = "E200"  # Algorithm not allowed
    VC_TIME = "E200"  # Credential temporally invalid
    VC_REVOKED = "E200"  # Credential revoked
    KEY_BINDING_UNVERIFIED = "E200"  # Key binding present but PoP not verified (limitation)
    
    # E300: ChainError - Incomplete or cyclic delegation chain
    CHAIN_ERROR = "E300"
    DG_DEPTH = "E300"  # Delegation depth exceeded
    DG_TIME = "E300"  # Delegation temporally invalid
    DG_REVOKED = "E300"  # Delegation revoked
    STATUS_FETCH_ERROR = "E300"  # Status fetch failed (when status_required=True)
    ANCHOR_NOT_FOUND = "E300"  # Chain fingerprint not anchored (when require_anchor=True)
    ANCHOR_VERIFICATION_FAILED = "E300"  # Anchor verification failed
    
    # E400: ScopeViolation - Operation exceeds delegated authority
    SCOPE_VIOLATION = "E400"
    DG_SCOPE_ESCALATION = "E400"  # Scope escalation not allowed
    
    # E500: PolicyError - Failed policy or issuer validation
    POLICY_ERROR = "E500"
    HOLDER_BINDING = "E500"  # Holder binding validation failed
    
    # E900: InternalError - Gateway failure or processing exception
    INTERNAL_ERROR = "E900"
    INTERNAL = "E900"  # Internal system errors

# Configuration constants
DETERMINISTIC_TIMESTAMP = 1735600000  # Fixed timestamp for determinism in tests
VRO_EXPIRATION_SECONDS = 3600  # 1 hour
