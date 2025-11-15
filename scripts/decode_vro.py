"""
Script to decode and display VRO JWT content.
"""

import json
import sys
from pathlib import Path

try:
    import jwt
except ImportError:
    print("Error: PyJWT is not installed. Install with: pip install pyjwt[crypto]")
    sys.exit(1)


def decode_vro_token(token: str) -> None:
    """
    Decodes and displays a VRO JWT.
    
    Args:
        token: VRO JWT token
    """
    try:
        header = jwt.get_unverified_header(token)
        payload = jwt.decode(token, options={"verify_signature": False})
        
        print("=" * 60)
        print("DECODED VRO JWT")
        print("=" * 60)
        print("\nHeader:")
        print(json.dumps(header, indent=2))
        print("\nPayload (VRO):")
        print(json.dumps(payload, indent=2))
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Decision: {payload.get('decision')}")
        print(f"Issuer: {payload.get('issuer')}")
        print(f"Subject: {payload.get('subject')}")
        print(f"Policy: {payload.get('policy_ref')}")
        print(f"Delegation Depth: {payload.get('delegation_chain_depth', 0)}")
        print(f"Assurance: {payload.get('assurance')}")
        if payload.get('chain_fingerprint'):
            print(f"Chain Fingerprint: {payload['chain_fingerprint']}")
        
    except Exception as e:
        print(f"Error decoding JWT: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/decode_vro.py <vro_jwt_token>")
        print("\nOr from a JSON response file:")
        print("  python scripts/decode_vro.py --file fixtures/response.json")
        sys.exit(1)
    
    token = None
    
    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("Error: file path required", file=sys.stderr)
            sys.exit(1)
        
        file_path = Path(sys.argv[2])
        if not file_path.exists():
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            token = data.get("vro_jwt")
            if not token:
                print("Error: 'vro_jwt' not found in file", file=sys.stderr)
                sys.exit(1)
    else:
        token = sys.argv[1]
    
    decode_vro_token(token)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDecoding interrupted by user")
        sys.exit(1)
