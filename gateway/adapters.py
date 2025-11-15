"""
Adapters for presentation normalization and CVC construction.
"""

import jwt
import json
import time
import logging
from typing import Tuple, Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AdapterError(Exception):
    """Base exception for adapter errors."""
    pass


def load_jwks(path: str) -> Dict[str, Any]:
    """
    Loads a JWKS file from the filesystem.
    
    Args:
        path: Path to JWKS file (relative or absolute)
        
    Returns:
        Dict with JWKS content
    """
    p = Path(path)
    if not p.is_absolute():
        base_dir = Path(__file__).parent.parent
        p = base_dir / path
    
    if not p.exists():
        raise AdapterError(f"JWKS file not found: {p}")
    
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, IOError) as e:
        raise AdapterError(f"Error loading JWKS from {p}: {str(e)}")


def detect_profile(presentation: Dict[str, Any]) -> str:
    """
    Detects the presentation profile of the credential.
    
    The Trust Gateway (L3) supports multiple credential encodings:
    - VC-JWT: Verifiable Credentials in JWT format
    - VC-LD: Verifiable Credentials in Linked Data format
    - SD-JWT: Selective Disclosure JWT (for delegation grants)
    
    Args:
        presentation: Dict with presentation (must have 'type')
        
    Returns:
        String with detected profile (e.g., "VC-JWT", "VC-LD")
        
    Raises:
        AdapterError: If profile is not supported
    """
    profile_type = presentation.get("type")
    
    if profile_type == "VC-JWT":
        return "VC-JWT"
    elif profile_type == "VC-LD":
        return "VC-LD"
    
    raise AdapterError(f"Unsupported presentation type: {profile_type}")


def normalize_vc_jwt(
    presentation: Dict[str, Any], 
    policy: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Normalizes a VC-JWT presentation to CVC format.
    
    Args:
        presentation: Dict with presentation (must have 'jwt')
        policy: Dict with policy (not currently used, but kept for consistency)
        
    Returns:
        Tuple (identity_dict, claims_list, proofs_list, status_dict)
        
    Raises:
        AdapterError: If there's an error normalizing the credential
    """
    try:
        jwt_token = presentation.get("jwt")
        if not jwt_token:
            raise AdapterError("Presentation missing 'jwt' field")
        
        # Decode without verification (verification happens in verifier)
        header = jwt.get_unverified_header(jwt_token)
        payload = jwt.decode(jwt_token, options={"verify_signature": False})
        
        # Extract identity
        issuer = payload.get("iss", "")
        subject = payload.get("sub", "")
        
        if not issuer or not subject:
            raise AdapterError("JWT payload missing 'iss' or 'sub'")
        
        identity = {
            "issuer": issuer,
            "subject": subject
        }
        
        # Extract claims
        vc_data = payload.get("vc", {})
        claims = [{
            "type": vc_data.get("type", []),
            "credentialSubject": vc_data.get("credentialSubject", {})
        }]
        
        # Extract proof information
        proofs = [{
            "format": "JWS",
            "alg": header.get("alg", "EdDSA"),
            "kid": header.get("kid")
        }]
        
        # Extract status information
        credential_status = vc_data.get("credentialStatus", {})
        status = {
            "statusListCredential": credential_status.get("statusListCredential"),
            "statusListIndex": credential_status.get("statusListIndex", 0),
            "fetched_at": int(time.time())
        }
        
        return (identity, claims, proofs, status)
    
    except jwt.InvalidTokenError as e:
        raise AdapterError(f"Invalid JWT format: {str(e)}")
    except Exception as e:
        raise AdapterError(f"Error normalizing VC-JWT: {str(e)}")


def parse_dg_jwts(delegation_tokens: List[str]) -> List[Dict[str, Any]]:
    """
    Parses a list of DG-SD-JWT tokens without verifying signatures.
    
    Args:
        delegation_tokens: List of delegation JWT tokens
        
    Returns:
        List of dicts with 'hdr', 'pld', and 'raw' for each delegation
    """
    parsed = []
    
    for token in delegation_tokens:
        try:
            header = jwt.get_unverified_header(token)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            parsed.append({
                "hdr": header,
                "pld": payload,
                "raw": token
            })
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid DG token format: {str(e)}")
            # Continue with next token
            continue
    
    return parsed


def normalize_vc_ld(
    presentation: Dict[str, Any], 
    policy: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Normalizes a VC-LD presentation to CVC format.
    
    This function demonstrates how the Trust Gateway normalizes different
    credential encodings (VC-LD) into the canonical CVC structure, making
    verification protocol-agnostic and format-independent.
    
    Args:
        presentation: Dict with presentation (must have 'credential')
        policy: Dict with policy (not currently used, but kept for consistency)
        
    Returns:
        Tuple (identity_dict, claims_list, proofs_list, status_dict)
        
    Raises:
        AdapterError: If there's an error normalizing the credential
    """
    try:
        credential = presentation.get("credential")
        if not credential:
            raise AdapterError("Presentation missing 'credential' field")
        
        # Extract identity from VC-LD structure
        issuer = credential.get("issuer", {})
        if isinstance(issuer, dict):
            issuer_id = issuer.get("id", issuer.get("@id", ""))
        else:
            issuer_id = str(issuer) if issuer else ""
        
        credential_subject = credential.get("credentialSubject", {})
        if isinstance(credential_subject, dict):
            subject_id = credential_subject.get("id", credential_subject.get("@id", ""))
        else:
            subject_id = str(credential_subject) if credential_subject else ""
        
        if not issuer_id or not subject_id:
            raise AdapterError("VC-LD credential missing issuer.id or credentialSubject.id")
        
        identity = {
            "issuer": issuer_id,
            "subject": subject_id
        }
        
        # Extract claims
        claims = [{
            "type": credential.get("type", []),
            "credentialSubject": credential_subject
        }]
        
        # Extract proof information (LD-Proof)
        proof = credential.get("proof", {})
        proof_type = proof.get("type", "BbsBlsSignature2020")
        
        proofs = [{
            "format": "LD-Proof",
            "type": proof_type,
            "proofValue": proof.get("proofValue"),
            "verificationMethod": proof.get("verificationMethod"),
            "created": proof.get("created")
        }]
        
        # Extract status information
        credential_status = credential.get("credentialStatus", {})
        status = {
            "statusListCredential": credential_status.get("statusListCredential"),
            "statusListIndex": credential_status.get("statusListIndex", 0),
            "fetched_at": int(time.time())
        }
        
        return (identity, claims, proofs, status)
    
    except Exception as e:
        raise AdapterError(f"Error normalizing VC-LD: {str(e)}")


def normalize_dg_ld(dg_ld: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a DG-LD (Linked Data delegation grant) to CVC format.
    
    Extracts issuer, subject, scope, constraints from DG-LD structure.
    Similar to normalize_vc_ld() but for delegation grants.
    
    Args:
        dg_ld: Dict with DG-LD structure
        
    Returns:
        Dict with normalized delegation structure compatible with CVC Delta
    """
    try:
        # Extract issuer
        issuer = dg_ld.get("issuer", {})
        if isinstance(issuer, dict):
            issuer_id = issuer.get("id", issuer.get("@id", ""))
        else:
            issuer_id = str(issuer) if issuer else ""
        
        # Extract subject
        credential_subject = dg_ld.get("credentialSubject", {})
        if isinstance(credential_subject, dict):
            subject_id = credential_subject.get("id", credential_subject.get("@id", ""))
            delegation = credential_subject.get("delegation", {})
        else:
            subject_id = str(credential_subject) if credential_subject else ""
            delegation = {}
        
        if not issuer_id or not subject_id:
            raise AdapterError("DG-LD missing issuer.id or credentialSubject.id")
        
        # Extract delegation details
        scope = delegation.get("scope", {})
        key_binding = delegation.get("keyBinding", {})
        status = delegation.get("status", {})
        constraints = delegation.get("constraints", {})
        
        # Parse dates (simplified - use current time if not available)
        # In production, use proper ISO8601 parsing
        nbf = 0
        exp = 0
        if dg_ld.get("validFrom"):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(dg_ld["validFrom"].replace("Z", "+00:00"))
                nbf = int(dt.timestamp())
            except:
                nbf = int(time.time())
        elif dg_ld.get("issuanceDate"):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(dg_ld["issuanceDate"].replace("Z", "+00:00"))
                nbf = int(dt.timestamp())
            except:
                nbf = int(time.time())
        
        if dg_ld.get("validUntil"):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(dg_ld["validUntil"].replace("Z", "+00:00"))
                exp = int(dt.timestamp())
            except:
                exp = int(time.time()) + 86400 * 365  # Default 1 year
        
        # Normalize to CVC Delta format (similar to DG-SD-JWT structure)
        normalized = {
            "hdr": {
                "alg": "LD-Proof",
                "type": dg_ld.get("proof", {}).get("type", "BbsBlsSignature2020")
            },
            "pld": {
                "iss": issuer_id,
                "sub": subject_id,
                "nbf": nbf,
                "exp": exp,
                "dg": {
                    "scope": scope,
                    "key_binding": key_binding,
                    "status": status,
                    "constraints": constraints
                }
            },
            "raw": dg_ld  # Keep original for reference
        }
        
        return normalized
    
    except Exception as e:
        raise AdapterError(f"Error normalizing DG-LD: {str(e)}")


def normalize_oidc4vp_response(
    vp_token: str,
    presentation_definition: Optional[Dict[str, Any]],
    policy_id: str
) -> Dict[str, Any]:
    """
    Normalizes OIDC4VP vp_token to standard VerificationRequest format.
    
    OIDC4VP vp_token can contain:
    - VC-JWT: Direct JWT token or VP-JWT with embedded credentials
    - VC-LD: JSON-LD Verifiable Presentation
    
    This function extracts the credential(s) and delegation chain,
    then constructs a VerificationRequest that can be processed
    by the standard verification flow.
    
    Args:
        vp_token: vp_token from OIDC4VP authorization response
        presentation_definition: Optional presentation definition for context
        policy_id: Policy ID to apply
        
    Returns:
        Dict in VerificationRequest format
    """
    try:
        # Try to decode as JWT first (VC-JWT or VP-JWT)
        try:
            header = jwt.get_unverified_header(vp_token)
            payload = jwt.decode(vp_token, options={"verify_signature": False})
            
            # Check if it's a Verifiable Presentation JWT
            if "vp" in payload:
                # VP-JWT format: extract credentials from vp.verifiableCredential
                vp_data = payload.get("vp", {})
                credentials = vp_data.get("verifiableCredential", [])
                
                if not credentials:
                    raise AdapterError("VP-JWT missing verifiableCredential")
                
                # Take first credential (can be extended for multiple)
                first_credential = credentials[0]
                
                # Check credential format
                if isinstance(first_credential, str):
                    # VC-JWT embedded as string
                    return {
                        "presentation": {
                            "type": "VC-JWT",
                            "jwt": first_credential
                        },
                        "policy_id": policy_id,
                        "delegation_chain": payload.get("delegation_chain"),
                        "holder_binding": payload.get("holder_binding")
                    }
                else:
                    # VC-LD embedded as object
                    return {
                        "presentation": {
                            "type": "VC-LD",
                            "credential": first_credential
                        },
                        "policy_id": policy_id,
                        "delegation_chain": payload.get("delegation_chain"),
                        "holder_binding": payload.get("holder_binding")
                    }
            else:
                # Direct VC-JWT (not wrapped in VP)
                return {
                    "presentation": {
                        "type": "VC-JWT",
                        "jwt": vp_token
                    },
                    "policy_id": policy_id,
                    "delegation_chain": None,
                    "holder_binding": None
                }
        
        except jwt.InvalidTokenError:
            # Not a JWT - try as JSON-LD Verifiable Presentation
            import json
            vp_ld = json.loads(vp_token) if isinstance(vp_token, str) else vp_token
            
            if vp_ld.get("type") and "VerifiablePresentation" in vp_ld.get("type", []):
                # Extract first credential from verifiableCredential array
                credentials = vp_ld.get("verifiableCredential", [])
                if not credentials:
                    raise AdapterError("VP-LD missing verifiableCredential")
                
                first_credential = credentials[0]
                
                return {
                    "presentation": {
                        "type": "VC-LD",
                        "credential": first_credential
                    },
                    "policy_id": policy_id,
                    "delegation_chain": None,
                    "holder_binding": None
                }
            else:
                raise AdapterError("Invalid VP-LD structure")
    
    except (json.JSONDecodeError, KeyError) as e:
        raise AdapterError(f"Invalid vp_token format: {str(e)}")
