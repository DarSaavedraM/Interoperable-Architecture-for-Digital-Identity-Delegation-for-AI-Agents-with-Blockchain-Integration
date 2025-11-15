"""
Script to generate a revoked VC-JWT.
"""

import json
import sys
from pathlib import Path
import jwt
from cryptography.hazmat.primitives import serialization


def mint_revoked_vc() -> None:
    """Generates a revoked VC-JWT and updates req_revoked.json."""
    base_dir = Path(__file__).parent.parent
    fixtures_dir = base_dir / "fixtures"
    requests_dir = fixtures_dir / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)
    
    # Load payload with revoked status
    vc_claims_file = fixtures_dir / "vc_jwt_bank.json"
    if not vc_claims_file.exists():
        raise FileNotFoundError(f"VC claims file not found: {vc_claims_file}")
    
    with open(vc_claims_file, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Verify it points to revoked status
    status_url = payload.get("vc", {}).get("credentialStatus", {}).get("statusListCredential", "")
    if "revoked" not in status_url:
        print("⚠ Warning: vc_jwt_bank.json does not point to statuslist2021_revoked.json")
        print(f"  Current status URL: {status_url}")
    
    # Load private key
    private_key_path = fixtures_dir / "keys/issuer_bank_ed25519_private.pem"
    if not private_key_path.exists():
        raise FileNotFoundError(f"Private key not found: {private_key_path}")
    
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    
    # Generate token
    token = jwt.encode(
        payload,
        key=private_key,
        algorithm="EdDSA",
        headers={"kid": "bank-ed25519-1", "typ": "JWT"}
    )
    
    # Update req_revoked.json
    revoked_request_file = requests_dir / "req_revoked.json"
    if revoked_request_file.exists():
        with open(revoked_request_file, "r", encoding="utf-8") as f:
            req_data = json.load(f)
    else:
        req_data = {
            "presentation": {"type": "VC-JWT", "jwt": ""},
            "policy_id": "P-001",
            "holder_binding": {"type": "JWS", "proof": "demo-nonce-signature"}
        }
    
    req_data["presentation"]["jwt"] = token
    
    with open(revoked_request_file, "w", encoding="utf-8") as f:
        json.dump(req_data, f, indent=2)
    
    print(f"[OK] Revoked VC-JWT generated and updated in req_revoked.json")
    print(f"  Token (first 100 chars): {token[:100]}...")


if __name__ == "__main__":
    try:
        mint_revoked_vc()
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)
