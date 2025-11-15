"""
Script to generate negative test case requests.
"""

import json
import sys
from pathlib import Path
import jwt
from cryptography.hazmat.primitives import serialization


def sign_delegation(claims_file: Path, private_key, kid: str) -> str:
    """Signs a delegation and returns the JWT token."""
    with open(claims_file, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    token = jwt.encode(
        payload,
        private_key,
        algorithm="EdDSA",
        headers={"kid": kid, "typ": "JWT"}
    )
    
    return token


def mint_negative_cases() -> None:
    """Generates all negative test case requests."""
    base_dir = Path(__file__).parent.parent
    fixtures_dir = base_dir / "fixtures"
    requests_dir = fixtures_dir / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)
    
    # Load private key
    private_key_path = fixtures_dir / "keys/issuer_bank_ed25519_private.pem"
    if not private_key_path.exists():
        raise FileNotFoundError(f"Private key not found: {private_key_path}")
    
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    
    kid = "bank-ed25519-1"
    
    # Load base VC-JWT request
    base_request_file = requests_dir / "req_vc_jwt_only.json"
    if not base_request_file.exists():
        raise FileNotFoundError(f"Base request file not found: {base_request_file}")
    
    with open(base_request_file, "r", encoding="utf-8") as f:
        base_request = json.load(f)
    
    # S4a: Expired DG
    dg_expired_token = sign_delegation(
        fixtures_dir / "dg_expired.json",
        private_key,
        kid
    )
    req_expired = {
        "presentation": base_request["presentation"],
        "policy_id": "P-001",
        "delegation_chain": [dg_expired_token],
        "holder_binding": base_request.get("holder_binding")
    }
    with open(requests_dir / "req_s4_expired_dg.json", "w", encoding="utf-8") as f:
        json.dump(req_expired, f, indent=2)
    
    # S4b: Revoked DG
    dg_revoked_token = sign_delegation(
        fixtures_dir / "dg_revoked.json",
        private_key,
        kid
    )
    req_revoked_dg = {
        "presentation": base_request["presentation"],
        "policy_id": "P-001",
        "delegation_chain": [dg_revoked_token],
        "holder_binding": base_request.get("holder_binding")
    }
    with open(requests_dir / "req_s4_revoked_dg.json", "w", encoding="utf-8") as f:
        json.dump(req_revoked_dg, f, indent=2)
    
    # S4c: Scope escalation
    # First create a valid DG1, then DG2 with escalation
    dg1_token = sign_delegation(
        fixtures_dir / "dg1_sdjwt.json",
        private_key,
        kid
    )
    dg_escalation_token = sign_delegation(
        fixtures_dir / "dg_scope_escalation.json",
        private_key,
        kid
    )
    req_escalation = {
        "presentation": base_request["presentation"],
        "policy_id": "P-001",
        "delegation_chain": [dg1_token, dg_escalation_token],
        "holder_binding": base_request.get("holder_binding")
    }
    with open(requests_dir / "req_s4_scope_escalation.json", "w", encoding="utf-8") as f:
        json.dump(req_escalation, f, indent=2)
    
    # S4d: Key binding mismatch (for documentation - PoP not verified)
    dg_keybinding_token = sign_delegation(
        fixtures_dir / "dg_key_binding_mismatch.json",
        private_key,
        kid
    )
    req_keybinding = {
        "presentation": base_request["presentation"],
        "policy_id": "P-001",
        "delegation_chain": [dg_keybinding_token],
        "holder_binding": base_request.get("holder_binding")
    }
    with open(requests_dir / "req_s4_key_binding.json", "w", encoding="utf-8") as f:
        json.dump(req_keybinding, f, indent=2)
    
    print("[OK] Negative test cases generated")
    print(f"  Expired DG: {requests_dir / 'req_s4_expired_dg.json'}")
    print(f"  Revoked DG: {requests_dir / 'req_s4_revoked_dg.json'}")
    print(f"  Scope escalation: {requests_dir / 'req_s4_scope_escalation.json'}")
    print(f"  Key binding: {requests_dir / 'req_s4_key_binding.json'}")


if __name__ == "__main__":
    try:
        mint_negative_cases()
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)


