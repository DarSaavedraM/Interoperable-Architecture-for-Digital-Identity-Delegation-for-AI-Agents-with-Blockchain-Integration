"""
Script to generate DG-LD (Linked Data format delegation grant).
"""

import json
import sys
from pathlib import Path


def mint_dg_ld() -> None:
    """Generates DG-LD fixture (normalization only, not full verification)."""
    base_dir = Path(__file__).parent.parent
    fixtures_dir = base_dir / "fixtures"
    requests_dir = fixtures_dir / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)
    
    # Load DG-LD fixture
    dg_ld_file = fixtures_dir / "dg_ld.json"
    if not dg_ld_file.exists():
        raise FileNotFoundError(f"DG-LD fixture not found: {dg_ld_file}")
    
    with open(dg_ld_file, "r", encoding="utf-8") as f:
        dg_ld = json.load(f)
    
    # Load base VC-LD request
    base_request_file = requests_dir / "req_vc_ld_only.json"
    if not base_request_file.exists():
        raise FileNotFoundError(f"Base VC-LD request not found: {base_request_file}")
    
    with open(base_request_file, "r", encoding="utf-8") as f:
        base_request = json.load(f)
    
    # Create request with VC-LD + DG-LD
    req_s2_dgld = {
        "presentation": base_request["presentation"],
        "policy_id": "P-001",
        "delegation_chain_ld": [dg_ld],
        "holder_binding": base_request.get("holder_binding")
    }
    
    output_file = requests_dir / "req_s2_ssi_dgld.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(req_s2_dgld, f, indent=2)
    
    # Also create VC-LD + DG-SD-JWT (hybrid)
    # Load DG-SD-JWT
    dg1_jwt_file = requests_dir / "dg1.jwt.json"
    if dg1_jwt_file.exists():
        with open(dg1_jwt_file, "r", encoding="utf-8") as f:
            dg1_data = json.load(f)
        
        req_s2_hybrid = {
            "presentation": base_request["presentation"],
            "policy_id": "P-001",
            "delegation_chain": [dg1_data["dg_jwt"]],
            "holder_binding": base_request.get("holder_binding")
        }
        
        output_file_hybrid = requests_dir / "req_s2_ssi_dgsdjwt.json"
        with open(output_file_hybrid, "w", encoding="utf-8") as f:
            json.dump(req_s2_hybrid, f, indent=2)
        
        print("[OK] DG-LD requests generated")
        print(f"  VC-LD + DG-LD: {output_file}")
        print(f"  VC-LD + DG-SD-JWT: {output_file_hybrid}")
    else:
        print("[OK] DG-LD request generated (DG-SD-JWT not available)")
        print(f"  VC-LD + DG-LD: {output_file}")


if __name__ == "__main__":
    try:
        mint_dg_ld()
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)


