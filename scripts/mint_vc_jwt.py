"""
Script to generate example VC-JWT credentials.
"""

import json
import sys
from pathlib import Path
import jwt
from cryptography.hazmat.primitives import serialization


def mint_vc_jwt() -> None:
    """Generates a VC-JWT and creates the request file."""
    base_dir = Path(__file__).parent.parent
    fixtures_dir = base_dir / "fixtures"
    requests_dir = fixtures_dir / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)
    
    # Load payload
    vc_claims_file = fixtures_dir / "vc_jwt_bank.json"
    if not vc_claims_file.exists():
        raise FileNotFoundError(f"VC claims file not found: {vc_claims_file}")
    
    with open(vc_claims_file, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
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
    
    # Create request
    request_data = {
        "presentation": {
            "type": "VC-JWT",
            "jwt": token
        },
        "policy_id": "P-001",
        "holder_binding": {
            "type": "JWS",
            "proof": "demo-nonce-signature"
        }
    }
    
    request_file = requests_dir / "req_vc_jwt_only.json"
    with open(request_file, "w", encoding="utf-8") as f:
        json.dump(request_data, f, indent=2)
    
    print(f"[OK] VC-JWT generated and saved to: {request_file}")
    print(f"  Token (first 100 chars): {token[:100]}...")


if __name__ == "__main__":
    try:
        mint_vc_jwt()
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)
