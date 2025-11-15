"""
Script to build JWKS files from Ed25519 public keys.
"""

import json
import base64
import sys
from pathlib import Path
from cryptography.hazmat.primitives import serialization


def b64u(data: bytes) -> str:
    """
    Encodes bytes to base64url without padding.
    
    Args:
        data: Bytes to encode
        
    Returns:
        Base64url string without padding
    """
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def ed25519_pem_to_jwk(pub_pem_path: Path, kid: str) -> dict:
    """
    Converts an Ed25519 public key in PEM format to JWK.
    
    Args:
        pub_pem_path: Path to PEM file of public key
        kid: Key ID for the JWK
        
    Returns:
        Dict with the JWK
    """
    with open(pub_pem_path, 'rb') as f:
        public_key = serialization.load_pem_public_key(f.read())
    
    # Get raw bytes of public key
    raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    return {
        "kty": "OKP",
        "crv": "Ed25519",
        "x": b64u(raw_bytes),
        "kid": kid,
        "alg": "EdDSA",
        "use": "sig"
    }


def build_jwks() -> None:
    """Builds JWKS files for issuer_bank and verifier."""
    base_dir = Path(__file__).parent.parent
    fixtures_dir = base_dir / "fixtures"
    keys_dir = fixtures_dir / "keys"
    
    # JWKS for issuer_bank
    bank_pub_key = keys_dir / "issuer_bank_ed25519_public.pem"
    if not bank_pub_key.exists():
        raise FileNotFoundError(f"Bank public key not found: {bank_pub_key}")
    
    jwk_bank = ed25519_pem_to_jwk(bank_pub_key, "bank-ed25519-1")
    jwks_bank_file = fixtures_dir / "jwks_issuer_bank.json"
    with open(jwks_bank_file, "w", encoding="utf-8") as f:
        json.dump({"keys": [jwk_bank]}, f, indent=2)
    print(f"[OK] JWKS generated: {jwks_bank_file}")
    
    # JWKS for verifier
    verifier_pub_key = keys_dir / "verifier_ed25519_public.pem"
    if not verifier_pub_key.exists():
        raise FileNotFoundError(f"Verifier public key not found: {verifier_pub_key}")
    
    jwk_verifier = ed25519_pem_to_jwk(verifier_pub_key, "verifier-ed25519-1")
    jwks_verifier_file = fixtures_dir / "jwks_verifier.json"
    with open(jwks_verifier_file, "w", encoding="utf-8") as f:
        json.dump({"keys": [jwk_verifier]}, f, indent=2)
    print(f"[OK] JWKS generated: {jwks_verifier_file}")


if __name__ == "__main__":
    try:
        build_jwks()
        print("[OK] JWKS files written successfully")
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)
