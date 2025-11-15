"""
Cryptographic utilities for JWT/JWS verification with Ed25519.
"""

import json
import base64
from typing import Dict, Any, Optional
from pathlib import Path
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


class CryptoError(Exception):
    """Base exception for cryptographic errors."""
    pass


class KeyNotFoundError(CryptoError):
    """Error when a key is not found in JWKS."""
    pass


def jwks_get_key(jwks_path: str, kid: str) -> bytes:
    """
    Retrieves a public key from a JWKS by kid and converts it to PEM format.
    
    Args:
        jwks_path: Path to JWKS file
        kid: Key ID to search for
        
    Returns:
        Public key in PEM format (bytes)
        
    Raises:
        KeyNotFoundError: If kid is not found in JWKS
        CryptoError: If there's an error processing the key
    """
    try:
        path = Path(jwks_path) if isinstance(jwks_path, str) else jwks_path
        data = json.loads(path.read_text())
        
        for key_data in data.get("keys", []):
            if key_data.get("kid") == kid:
                return _jwk_to_pem(key_data)
        
        raise KeyNotFoundError(f"KID '{kid}' not found in JWKS: {jwks_path}")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise CryptoError(f"Error loading JWKS from {jwks_path}: {str(e)}")


def _jwk_to_pem(jwk: Dict[str, Any]) -> bytes:
    """
    Converts an Ed25519 JWK to PEM format.
    
    Args:
        jwk: Dict with the JWK
        
    Returns:
        Public key in PEM format
    """
    from cryptography.hazmat.primitives.asymmetric import ed25519
    
    x = jwk.get("x", "")
    if not x:
        raise CryptoError("JWK missing 'x' coordinate")
    
    # Padding for base64url
    x_padded = x + '=' * (4 - len(x) % 4)
    try:
        public_bytes = base64.urlsafe_b64decode(x_padded)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
        
        # Convert to PEM for PyJWT
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem
    except Exception as e:
        raise CryptoError(f"Error converting JWK to PEM: {str(e)}")


def key_exists_in_jwks(jwks_path: str, kid: str) -> bool:
    """
    Checks if a key ID (kid) exists in a JWKS.
    
    This is a basic proof-of-possession validation: it verifies that
    the key referenced in key_binding.kid exists in the delegate's JWKS.
    Full PoP would require the delegate to prove control of the key through
    a challenge-response mechanism (e.g., DPoP, mTLS).
    
    Args:
        jwks_path: Path to JWKS file
        kid: Key ID to search for
        
    Returns:
        True if kid exists in JWKS, False otherwise
    """
    try:
        path = Path(jwks_path) if isinstance(jwks_path, str) else jwks_path
        data = json.loads(path.read_text())
        
        for key_data in data.get("keys", []):
            if key_data.get("kid") == kid:
                return True
        return False
    except (json.JSONDecodeError, FileNotFoundError):
        return False


def verify_jws(token: str, jwks_path: str) -> Dict[str, Any]:
    """
    Verifies and decodes a JWS (signed JWT).
    
    Args:
        token: JWT token to verify
        jwks_path: Path to JWKS file with public key
        
    Returns:
        Dict with 'header' and 'payload' of verified token
        
    Raises:
        CryptoError: If verification fails
    """
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise CryptoError("JWT header missing 'kid'")
        
        key = jwks_get_key(jwks_path, kid)
        payload = jwt.decode(token, key=key, algorithms=["EdDSA"])
        
        return {
            "header": header,
            "payload": payload
        }
    except jwt.InvalidTokenError as e:
        raise CryptoError(f"JWT verification failed: {str(e)}")
