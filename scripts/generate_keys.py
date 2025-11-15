"""
Script to generate Ed25519 key pairs.
"""

import sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def generate_keypair(prefix: str, keys_dir: Path) -> None:
    """
    Generates an Ed25519 key pair and saves them in PEM format.
    
    Args:
        prefix: Prefix for file names (e.g., "issuer_bank")
        keys_dir: Directory to save keys
    """
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Save private key
    private_path = keys_dir / f"{prefix}_ed25519_private.pem"
    with open(private_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"[OK] Private key generated: {private_path}")
    
    # Save public key
    public_path = keys_dir / f"{prefix}_ed25519_public.pem"
    with open(public_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    print(f"[OK] Public key generated: {public_path}")


def main() -> None:
    """Main function."""
    base_dir = Path(__file__).parent.parent
    keys_dir = base_dir / "fixtures/keys"
    
    print("Generating Ed25519 key pairs...")
    print("=" * 50)
    
    # Generate keys for issuer_bank
    generate_keypair("issuer_bank", keys_dir)
    
    # Generate keys for verifier
    generate_keypair("verifier", keys_dir)
    
    print("\n" + "=" * 50)
    print("[OK] Keys generated successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)
