"""
Generate a batch of verification requests with blockchain anchor as a variable.

This script extends the base batch generation to include blockchain anchor
as a configurable variable for statistical analysis.
"""

import json
import sys
import random
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import jwt
from cryptography.hazmat.primitives import serialization

# Import base configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from batch.config import (
        RANDOM_SEED, NUM_REQUESTS, PROFILE_DISTRIBUTION, CHAIN_DEPTH_DISTRIBUTION,
        ANCHOR_DISTRIBUTION, AVAILABLE_ACTIONS, SCOPE_RESOURCES,
        POLICY_WITHOUT_ANCHOR, POLICY_WITH_ANCHOR
    )
except ImportError:
    # Fallback if running directly
    from config import (
        RANDOM_SEED, NUM_REQUESTS, PROFILE_DISTRIBUTION, CHAIN_DEPTH_DISTRIBUTION,
        ANCHOR_DISTRIBUTION, AVAILABLE_ACTIONS, SCOPE_RESOURCES,
        POLICY_WITHOUT_ANCHOR, POLICY_WITH_ANCHOR
    )


def load_private_key(fixtures_dir: Path) -> Any:
    """Load the issuer private key."""
    key_path = fixtures_dir / "keys/issuer_bank_ed25519_private.pem"
    if not key_path.exists():
        raise FileNotFoundError(f"Private key not found: {key_path}")
    
    with open(key_path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def generate_vc_jwt_payload(
    base_payload: Dict[str, Any],
    variation_id: int
) -> Dict[str, Any]:
    """Generate a VC-JWT payload with controlled variations."""
    payload = json.loads(json.dumps(base_payload))  # Deep copy
    
    # Vary subject ID slightly (for diversity, but keep valid)
    if variation_id % 10 == 0:
        payload["sub"] = f"did:example:holder_{variation_id % 100}"
    
    # Vary credential subject data slightly
    if "vc" in payload and "credentialSubject" in payload["vc"]:
        cs = payload["vc"]["credentialSubject"]
        if variation_id % 5 == 0:
            cs["accountVerified"] = True
            cs["accountId"] = f"ACC-{variation_id:04d}"
    
    return payload


def generate_dg_payload(
    base_dg: Dict[str, Any],
    depth: int,
    parent_scope: Dict[str, Any],
    variation_id: int,
    is_first: bool = False
) -> Dict[str, Any]:
    """Generate a DG payload with controlled scope containment."""
    payload = json.loads(json.dumps(base_dg))  # Deep copy
    
    # Ensure required "dg" field exists
    if "dg" not in payload:
        payload["dg"] = {}
    
    # Ensure scope exists in dg
    if "scope" not in payload["dg"]:
        payload["dg"]["scope"] = {}
    
    # Ensure scope containment: child scope must be subset of parent
    if not is_first:
        # Get parent scope actions
        parent_actions = set(parent_scope.get("actions", []))
        # Child can only use subset of parent actions
        available_actions = [a for a in AVAILABLE_ACTIONS if a in parent_actions]
        if not available_actions:
            available_actions = ["view"]  # Minimal fallback
        
        # Select subset of actions
        num_actions = min(len(available_actions), max(1, len(available_actions) - (variation_id % 2)))
        selected_actions = random.sample(available_actions, num_actions)
        
        payload["dg"]["scope"]["actions"] = selected_actions
        payload["dg"]["scope"]["resource"] = parent_scope.get("resource", "payments:transfer")
    else:
        # First DG: use parent scope or default
        if "actions" not in payload["dg"]["scope"]:
            payload["dg"]["scope"]["actions"] = parent_scope.get("actions", ["initiate", "quote", "approve"])
        if "resource" not in payload["dg"]["scope"]:
            payload["dg"]["scope"]["resource"] = parent_scope.get("resource", "payments:transfer")
    
    # Ensure required temporal fields
    if "nbf" not in payload:
        payload["nbf"] = 1735600000  # Default: 2025-01-01
    if "exp" not in payload:
        payload["exp"] = 1893456000  # Default: 2030-01-01
    
    # Ensure required issuer/subject
    if "iss" not in payload:
        payload["iss"] = "did:example:holder" if is_first else f"did:example:agent{depth-1}"
    
    # Vary delegate subject
    payload["sub"] = f"did:example:agent{depth}_{variation_id % 100}"
    
    # Ensure status field exists in dg
    if "status" not in payload["dg"]:
        payload["dg"]["status"] = {
            "type": "StatusList2021",
            "url": "https://localhost/status/statuslist2021_active.json"
        }
    
    # Ensure key_binding exists (optional but good to have)
    if "key_binding" not in payload["dg"]:
        payload["dg"]["key_binding"] = {"kid": f"agent{depth}-ed25519-1"}
    
    return payload


def generate_vc_jwt_request(
    base_vc_jwt: Dict[str, Any],
    private_key: Any,
    variation_id: int
) -> Tuple[Dict[str, Any], str]:
    """Generate a VC-JWT request."""
    payload = generate_vc_jwt_payload(base_vc_jwt, variation_id)
    
    token = jwt.encode(
        payload,
        private_key,
        algorithm="EdDSA",
        headers={"kid": "bank-ed25519-1", "typ": "JWT"}
    )
    
    request = {
        "presentation": {
            "type": "VC-JWT",
            "jwt": token
        },
        "policy_id": POLICY_WITHOUT_ANCHOR,  # Default, will be overridden if anchor required
        "holder_binding": {
            "type": "JWS",
            "proof": f"demo-nonce-{variation_id}"
        }
    }
    
    return request, "VC-JWT"


def generate_vc_ld_request(
    base_vc_ld: Dict[str, Any],
    variation_id: int
) -> Tuple[Dict[str, Any], str]:
    """Generate a VC-LD request."""
    vc_ld = json.loads(json.dumps(base_vc_ld))  # Deep copy
    
    # Vary subject
    if "credentialSubject" in vc_ld:
        vc_ld["credentialSubject"]["id"] = f"did:example:holder_{variation_id % 100}"
    
    request = {
        "presentation": {
            "type": "VC-LD",
            "credential": vc_ld
        },
        "policy_id": POLICY_WITHOUT_ANCHOR,  # Default, will be overridden if anchor required
        "holder_binding": {
            "type": "JWS",
            "proof": f"demo-nonce-{variation_id}"
        }
    }
    
    return request, "VC-LD"


def generate_delegation_chain(
    base_dg1: Dict[str, Any],
    base_dg2: Dict[str, Any],
    private_key: Any,
    depth: int,
    variation_id: int
) -> List[str]:
    """Generate a delegation chain of specified depth."""
    if depth == 0:
        return []
    
    chain = []
    # Initial parent scope (from holder)
    parent_scope = {"resource": "payments:transfer", "actions": ["initiate", "quote", "approve"]}
    
    for i in range(depth):
        is_first = (i == 0)
        
        if is_first:
            dg_payload = generate_dg_payload(base_dg1, i, parent_scope, variation_id, is_first=True)
        else:
            dg_payload = generate_dg_payload(base_dg2, i, parent_scope, variation_id, is_first=False)
        
        # Update parent scope for next iteration
        if "dg" in dg_payload:
            parent_scope = dg_payload["dg"]["scope"]
        else:
            parent_scope = dg_payload.get("scope", {"resource": "payments:transfer", "actions": ["initiate", "quote", "approve"]})
        
        # Sign DG
        token = jwt.encode(
            dg_payload,
            private_key,
            algorithm="EdDSA",
            headers={"kid": "bank-ed25519-1", "typ": "JWT"}
        )
        
        chain.append(token)
    
    return chain


def ensure_anchor_policy(base_dir: Path) -> None:
    """Ensure anchor policy exists."""
    policy_file = base_dir / "fixtures" / "policy_P001ANCHOR.json"
    
    if not policy_file.exists():
        policy_with_anchor = {
            "id": "P-001-ANCHOR",
            "trusted_issuers": ["did:example:bank"],
            "alg_allowlist": ["EdDSA"],
            "holder_binding_required": True,
            "max_delegation_depth": 3,
            "status_ttl_seconds": 120,
            "clock_skew_seconds": 5,
            "require_anchor": True,
            "status_required": True
        }
        policy_file.write_text(json.dumps(policy_with_anchor, indent=2))
        print(f"Created anchor policy: {policy_file}")


def generate_batch_requests(
    num_requests: int = NUM_REQUESTS,
    seed: int = RANDOM_SEED,
    include_anchor: bool = True
) -> None:
    """
    Generate batch requests with blockchain anchor as a variable.
    
    Args:
        num_requests: Number of requests to generate
        seed: Random seed for reproducibility
        include_anchor: Whether to include anchor as a variable
    """
    random.seed(seed)
    
    base_dir = Path(__file__).parent.parent.parent
    fixtures_dir = base_dir / "fixtures"
    requests_dir = fixtures_dir / "requests" / "batch"
    requests_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure anchor policy exists
    if include_anchor:
        ensure_anchor_policy(base_dir)
    
    # Load base credentials
    vc_jwt_file = fixtures_dir / "vc_jwt_bank.json"
    vc_ld_file = fixtures_dir / "vc_ld_bank.json"
    # Try both possible locations for DG files
    dg1_file = fixtures_dir / "requests" / "dg1.jwt.json"
    if not dg1_file.exists():
        dg1_file = fixtures_dir / "dg1_sdjwt.json"
    dg2_file = fixtures_dir / "requests" / "dg2.jwt.json"
    if not dg2_file.exists():
        dg2_file = fixtures_dir / "dg2_sdjwt.json"
    
    with open(vc_jwt_file, "r", encoding="utf-8") as f:
        base_vc_jwt = json.load(f)
    
    base_vc_ld = None
    if vc_ld_file.exists():
        with open(vc_ld_file, "r", encoding="utf-8") as f:
            base_vc_ld = json.load(f)
    
    with open(dg1_file, "r", encoding="utf-8") as f:
        base_dg1 = json.load(f)
    
    with open(dg2_file, "r", encoding="utf-8") as f:
        base_dg2 = json.load(f)
    
    # Load private key
    private_key = load_private_key(fixtures_dir)
    
    # Generate requests
    requests_metadata = []
    anchor_counts = {True: 0, False: 0}
    
    print(f"Generating {num_requests} requests with seed={seed}...")
    if include_anchor:
        print(f"Anchor distribution: {ANCHOR_DISTRIBUTION}")
    print("=" * 70)
    
    for i in range(num_requests):
        # Select profile based on distribution
        profile_rand = random.random()
        if profile_rand < PROFILE_DISTRIBUTION["VC-JWT"]:
            use_vc_jwt = True
        else:
            use_vc_jwt = False
            if base_vc_ld is None:
                use_vc_jwt = True  # Fallback if VC-LD not available
        
        # Select chain depth based on distribution
        depth_rand = random.random()
        cumulative = 0
        chain_depth = 0
        for depth, prob in CHAIN_DEPTH_DISTRIBUTION.items():
            cumulative += prob
            if depth_rand < cumulative:
                chain_depth = depth
                break
        
        # Select anchor requirement (only if include_anchor and chain_depth > 0)
        require_anchor = False
        if include_anchor and chain_depth > 0:
            anchor_rand = random.random()
            if anchor_rand < ANCHOR_DISTRIBUTION[True]:
                require_anchor = True
            anchor_counts[require_anchor] += 1
        
        # Generate request
        if use_vc_jwt:
            request, profile = generate_vc_jwt_request(base_vc_jwt, private_key, i)
        else:
            request, profile = generate_vc_ld_request(base_vc_ld, i)
        
        # Set policy based on anchor requirement
        if require_anchor:
            request["policy_id"] = POLICY_WITH_ANCHOR
        else:
            request["policy_id"] = POLICY_WITHOUT_ANCHOR
        
        # Add delegation chain if depth > 0
        if chain_depth > 0:
            chain = generate_delegation_chain(base_dg1, base_dg2, private_key, chain_depth, i)
            request["delegation_chain"] = chain
        
        # Save request
        request_file = requests_dir / f"req_batch_{i:04d}.json"
        with open(request_file, "w", encoding="utf-8") as f:
            json.dump(request, f, indent=2)
        
        # Record metadata
        requests_metadata.append({
            "request_id": f"batch_{i:04d}",
            "file": str(request_file.relative_to(base_dir)),
            "profile": profile,
            "chain_depth": chain_depth,
            "require_anchor": require_anchor if include_anchor and chain_depth > 0 else None,
            "variation_id": i
        })
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{num_requests} requests...")
    
    # Save metadata
    metadata_file = requests_dir / "batch_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        metadata = {
            "total_requests": num_requests,
            "random_seed": seed,
            "include_anchor": include_anchor,
            "distribution": {
                "profile": PROFILE_DISTRIBUTION,
                "chain_depth": CHAIN_DEPTH_DISTRIBUTION
            },
            "requests": requests_metadata
        }
        if include_anchor:
            metadata["distribution"]["anchor"] = ANCHOR_DISTRIBUTION
        json.dump(metadata, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 70)
    print("BATCH GENERATION SUMMARY")
    print("=" * 70)
    
    profile_counts = {}
    depth_counts = {}
    for meta in requests_metadata:
        profile_counts[meta["profile"]] = profile_counts.get(meta["profile"], 0) + 1
        depth_counts[meta["chain_depth"]] = depth_counts.get(meta["chain_depth"], 0) + 1
    
    print(f"\nTotal Requests: {num_requests}")
    print(f"Random Seed: {seed}")
    print(f"Include Anchor: {include_anchor}")
    
    print(f"\nProfile Distribution:")
    for profile, count in sorted(profile_counts.items()):
        print(f"  {profile}: {count} ({count/num_requests*100:.1f}%)")
    
    print(f"\nChain Depth Distribution:")
    for depth in sorted(depth_counts.keys()):
        count = depth_counts[depth]
        print(f"  Depth {depth}: {count} ({count/num_requests*100:.1f}%)")
    
    if include_anchor:
        total_with_chain = sum(1 for m in requests_metadata if m.get("chain_depth", 0) > 0)
        if total_with_chain > 0:
            print(f"\nAnchor Distribution (for requests with chain):")
            print(f"  With anchor: {anchor_counts[True]} ({anchor_counts[True]/total_with_chain*100:.1f}%)")
            print(f"  Without anchor: {anchor_counts[False]} ({anchor_counts[False]/total_with_chain*100:.1f}%)")
    
    print(f"\n[OK] Batch requests generated")
    print(f"  Directory: {requests_dir}")
    print(f"  Metadata: {metadata_file}")
    print(f"\nNext step: Run metrics collection:")
    print(f"  python scripts/batch/run_batch_metrics.py")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate batch requests with blockchain anchor as variable"
    )
    parser.add_argument(
        "--num-requests",
        type=int,
        default=NUM_REQUESTS,
        help=f"Number of requests to generate (default: {NUM_REQUESTS})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed for reproducibility (default: {RANDOM_SEED})"
    )
    parser.add_argument(
        "--no-anchor",
        action="store_true",
        help="Disable anchor as a variable (default: anchor is included)"
    )
    
    args = parser.parse_args()
    
    try:
        generate_batch_requests(
            num_requests=args.num_requests,
            seed=args.seed,
            include_anchor=not args.no_anchor
        )
    except KeyboardInterrupt:
        print("\n\nGeneration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

