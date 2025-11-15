"""
Pydantic schemas for request and response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any, Dict, Union


class PresentationJWT(BaseModel):
    """Credential presentation in JWT format."""
    type: Literal["VC-JWT"]
    jwt: str = Field(..., description="JWT token of the verifiable credential")


class PresentationLD(BaseModel):
    """Credential presentation in Linked Data (VC-LD) format."""
    type: Literal["VC-LD"]
    credential: Dict[str, Any] = Field(..., description="Verifiable Credential in JSON-LD format")


class VerificationRequest(BaseModel):
    """Credential verification request.
    
    The Trust Gateway (L3) accepts requests in different formats and normalizes
    them into the Canonical Verification Context (CVC), making verification
    protocol-agnostic and format-independent.
    """
    presentation: Union[PresentationJWT, PresentationLD] = Field(..., description="Credential presentation")
    policy_id: str = Field(..., description="Policy ID to apply")
    delegation_chain: Optional[List[str]] = Field(
        default=None,
        description="DG-SD-JWT delegation chain (in order)"
    )
    holder_binding: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Holder binding information (simplified for Milestone A)"
    )


class OIDC4VPResponse(BaseModel):
    """OIDC4VP authorization response."""
    vp_token: str = Field(..., description="Verifiable Presentation token")
    presentation_definition: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Presentation definition used in request"
    )
    state: Optional[str] = Field(default=None, description="OIDC state parameter")
    policy_id: str = Field(default="P-001", description="Policy ID to apply")


class CVC(BaseModel):
    """
    Canonical Verification Context (CVC).
    
    Standardized verification context that normalizes different
    presentation formats into a common structure.
    """
    I_issuer: str = Field(..., description="Issuer identifier")
    I_subject: str = Field(..., description="Subject identifier")
    C: List[Dict[str, Any]] = Field(..., description="Normalized claims")
    pi: List[Dict[str, Any]] = Field(..., description="Proof descriptors")
    Delta: List[Dict[str, Any]] = Field(..., description="Parsed delegations")
    P: Dict[str, Any] = Field(..., description="Loaded policy")
    S: Dict[str, Any] = Field(..., description="Status references")
    M: Dict[str, Any] = Field(..., description="Metadata (timestamps, request_id, etc.)")
