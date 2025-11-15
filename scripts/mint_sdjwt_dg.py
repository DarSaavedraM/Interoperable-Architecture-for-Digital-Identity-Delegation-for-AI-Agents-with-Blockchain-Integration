"""
Script to generate DG-SD-JWT delegation chains.
"""

import json
import sys
from pathlib import Path
import jwt
from cryptography.hazmat.primitives import serialization


def sign_delegation(
    claims_file: Path,
    output_file: Path,
    private_key,
    kid: str
) -> str:
    """
    Signs a delegation and saves the result.
    
    Returns:
        Generated JWT token
    """
    with open(claims_file, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    token = jwt.encode(
        payload,
        private_key,
        algorithm="EdDSA",
        headers={"kid": kid, "typ": "JWT"}
    )
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"dg_jwt": token}, f, indent=2)
    
    return token


def mint_delegation_chain() -> None:
    """Generates the complete delegation chain."""
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
    
    # Generate DG1 (holder -> agent1)
    dg1_token = sign_delegation(
        fixtures_dir / "dg1_sdjwt.json",
        requests_dir / "dg1.jwt.json",
        private_key,
        kid
    )
    
    # Generate DG2 (agent1 -> agent2)
    dg2_token = sign_delegation(
        fixtures_dir / "dg2_sdjwt.json",
        requests_dir / "dg2.jwt.json",
        private_key,
        kid
    )
    
    # Build request with VC + delegation chain
    base_request_file = requests_dir / "req_vc_jwt_only.json"
    if not base_request_file.exists():
        raise FileNotFoundError(f"Base request file not found: {base_request_file}")
    
    with open(base_request_file, "r", encoding="utf-8") as f:
        base_request = json.load(f)
    
    request_with_chain = {
        "presentation": base_request["presentation"],
        "policy_id": "P-001",
        "delegation_chain": [dg1_token, dg2_token],
        "holder_binding": {
            "type": "JWS",
            "proof": "demo-nonce-signature"
        }
    }
    
    output_file = requests_dir / "req_vc_jwt_plus_dg_chain.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(request_with_chain, f, indent=2)
    
    print("[OK] Delegation chain generated")
    print(f"  DG1: {dg1_token[:50]}...")
    print(f"  DG2: {dg2_token[:50]}...")
    print(f"  Request saved to: {output_file}")


if __name__ == "__main__":
    try:
        mint_delegation_chain()
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)
