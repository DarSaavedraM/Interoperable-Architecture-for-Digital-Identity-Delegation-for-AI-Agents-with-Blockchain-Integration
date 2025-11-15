"""
Trust Gateway - FastAPI-based API for credential verification.
"""

import logging
import time
import traceback
import json
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from gateway.schemas import VerificationRequest, OIDC4VPResponse
from gateway.policy import load_policy, PolicyError
from gateway.adapters import (
    detect_profile, 
    normalize_vc_jwt,
    normalize_vc_ld,
    parse_dg_jwts,
    normalize_oidc4vp_response,
    AdapterError
)
from gateway.config import JWKS_BANK, JWKS_VERIFIER, get_anchor_storage_path, is_anchor_enabled
from gateway.metrics_instrumentation import (
    get_metrics_collector,
    record_request_size,
    record_cvc_size,
    record_vc_jwt_size,
    record_dg_chain_size,
    record_vro_size
)
from verifier.verifier import verify_cvc
from verifier.anchor import create_mock_anchor, set_anchor_instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # INFO level to see important metrics
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration
)
logger = logging.getLogger(__name__)
# Set uvicorn logging to INFO as well
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

# Log that the module loaded
logger.info("=" * 70)
logger.info("[SERVER] Gateway module loaded - Metrics logging enabled")
logger.info("=" * 70)

# Initialize anchor if enabled
if is_anchor_enabled():
    anchor_storage = get_anchor_storage_path()
    anchor_instance = create_mock_anchor(storage_path=anchor_storage)
    set_anchor_instance(anchor_instance)
    logger.info(f"Blockchain anchor initialized (mock) - storage: {anchor_storage}")
else:
    logger.info("Blockchain anchor disabled")
    set_anchor_instance(None)

# Initialize FastAPI application
app = FastAPI(
    title="Trust Gateway API",
    description="API for verifying VC-JWT credentials and DG-SD-JWT delegation chains",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_cvc(
    request: VerificationRequest,
    policy: Dict[str, Any],
    profile: str
) -> Dict[str, Any]:
    """
    Builds a Canonical Verification Context (CVC) from the request.
    
    The CVC follows the formal structure: CVC={I_issuer,I_subject,C,π,Δ,P,S,M}
    where each component normalizes information from different protocols and formats.
    
    Once normalized to CVC, verification is deterministic and independent of:
    - Transport protocol (OIDC4VP, DIDComm, HTTPS)
    - Credential encoding (VC-JWT, VC-LD, SD-JWT)
    
    Args:
        request: Verification request
        policy: Loaded policy
        profile: Detected profile
        
    Returns:
        Dict with the structured CVC according to the conceptual model
    """
    # Normalize based on detected profile
    # This demonstrates protocol-agnostic normalization to CVC
    if profile == "VC-JWT":
        ident, claims, proofs, status = normalize_vc_jwt(
            request.presentation.model_dump(),
            policy
        )
        # Build metadata for VC-JWT
        holder_binding_dict = None
        if request.holder_binding:
            # holder_binding is already a dict from Pydantic model
            if isinstance(request.holder_binding, dict):
                holder_binding_dict = request.holder_binding
            else:
                holder_binding_dict = request.holder_binding.model_dump()
        
        metadata = {
            "request_id": str(int(time.time() * 1000)),
            "profile_hint": profile,
            "raw_vc_jwt": request.presentation.jwt,
            "holder_binding_ok": bool(request.holder_binding) if request.holder_binding else False,
            "holder_binding": holder_binding_dict
        }
    elif profile == "VC-LD":
        ident, claims, proofs, status = normalize_vc_ld(
            request.presentation.model_dump(),
            policy
        )
        # Build metadata for VC-LD
        holder_binding_dict = None
        if request.holder_binding:
            # holder_binding is already a dict from Pydantic model
            if isinstance(request.holder_binding, dict):
                holder_binding_dict = request.holder_binding
            else:
                holder_binding_dict = request.holder_binding.model_dump()
        
        metadata = {
            "request_id": str(int(time.time() * 1000)),
            "profile_hint": profile,
            "raw_vc_ld": request.presentation.model_dump().get("credential"),
            "holder_binding_ok": bool(request.holder_binding) if request.holder_binding else False,
            "holder_binding": holder_binding_dict
        }
    else:
        raise AdapterError(f"Unsupported profile for CVC construction: {profile}")
    
    # Parse delegation chain
    delta = parse_dg_jwts(request.delegation_chain or [])
    
    # Build CVC
    cvc = {
        "I_issuer": ident["issuer"],
        "I_subject": ident["subject"],
        "C": claims,
        "pi": proofs,
        "Delta": delta,
        "P": policy,
        "S": status,
        "M": metadata
    }
    
    return cvc


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with service information."""
    return {
        "service": "Trust Gateway API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": int(time.time())
    }




@app.get("/metrics/current")
async def get_current_metrics() -> Dict[str, Any]:
    """
    Get current metrics from the last request.
    
    This endpoint allows the metrics collection script to read
    metrics captured by the server after each request.
    """
    collector = get_metrics_collector()
    if not collector or not collector.current:
        logger.warning("[METRICS] /metrics/current called but no metrics available")
        return {"current": None}
    
    logger.info(f"[METRICS] /metrics/current called for request_id={collector.current.request_id}")
    
    # Serialize current metrics
    current = collector.current
    return {
        "current": {
            "request_id": current.request_id,
            "scenario": current.scenario,
            "profile": current.profile,
            "chain_depth": current.chain_depth,
            "e2e_latency": {
                "start_time": current.e2e_latency.start_time,
                "end_time": current.e2e_latency.end_time,
                "duration_ms": current.e2e_latency.duration_ms
            },
            "normalization_latency": {
                "start_time": current.normalization_latency.start_time,
                "end_time": current.normalization_latency.end_time,
                "duration_ms": current.normalization_latency.duration_ms
            },
            "verification_latency": {
                "start_time": current.verification_latency.start_time,
                "end_time": current.verification_latency.end_time,
                "duration_ms": current.verification_latency.duration_ms
            },
            "vro_signing_latency": {
                "start_time": current.vro_signing_latency.start_time,
                "end_time": current.vro_signing_latency.end_time,
                "duration_ms": current.vro_signing_latency.duration_ms
            },
            "status_fetch_latency": {
                "duration_ms": current.status_fetch_latency.duration_ms
            },
            "sizes": {
                "vc_jwt_size_bytes": current.sizes.vc_jwt_size_bytes,
                "dg_chain_size_bytes": current.sizes.dg_chain_size_bytes,
                "vro_jwt_size_bytes": current.sizes.vro_jwt_size_bytes,
                "cvc_serialized_size_bytes": current.sizes.cvc_serialized_size_bytes,
                "request_size_bytes": current.sizes.request_size_bytes
            },
            "invariants": {
                "scope_containment_passed": current.invariants.scope_containment_passed,
                "temporal_validity_passed": current.invariants.temporal_validity_passed,
                "signature_verification_passed": current.invariants.signature_verification_passed,
                "chain_integrity_passed": current.invariants.chain_integrity_passed,
                "structural_validity_passed": current.invariants.structural_validity_passed,
                "fail_closed_operation": current.invariants.fail_closed_operation
            },
            "success": current.success,
            "error_code": current.error_code,
            "vro_hash": current.vro_hash,
            "chain_fingerprint": current.chain_fingerprint
        }
    }


@app.post("/metrics/clear")
async def clear_current_metrics() -> Dict[str, str]:
    """
    Clear current metrics after they've been read.
    
    This endpoint allows the metrics collection script to clear
    the server's current metrics after copying them.
    """
    collector = get_metrics_collector()
    if collector:
        collector.current = None
    return {"status": "cleared"}


def serialize_metrics(collector) -> Optional[Dict[str, Any]]:
    """Serialize current metrics for API response."""
    if not collector or not collector.current:
        return None
    
    current = collector.current
    return {
        "request_id": current.request_id,
        "scenario": current.scenario,
        "profile": current.profile,
        "chain_depth": current.chain_depth,
        "e2e_latency": {
            "start_time": current.e2e_latency.start_time,
            "end_time": current.e2e_latency.end_time,
            "duration_ms": current.e2e_latency.duration_ms
        },
        "normalization_latency": {
            "start_time": current.normalization_latency.start_time,
            "end_time": current.normalization_latency.end_time,
            "duration_ms": current.normalization_latency.duration_ms
        },
        "verification_latency": {
            "start_time": current.verification_latency.start_time,
            "end_time": current.verification_latency.end_time,
            "duration_ms": current.verification_latency.duration_ms
        },
        "vro_signing_latency": {
            "start_time": current.vro_signing_latency.start_time,
            "end_time": current.vro_signing_latency.end_time,
            "duration_ms": current.vro_signing_latency.duration_ms
        },
        "status_fetch_latency": {
            "start_time": getattr(current.status_fetch_latency, "start_time", 0.0),
            "end_time": getattr(current.status_fetch_latency, "end_time", 0.0),
            "duration_ms": getattr(current.status_fetch_latency, "duration_ms", 0.0)
        },
        "sizes": {
            "vc_jwt_size_bytes": current.sizes.vc_jwt_size_bytes,
            "dg_chain_size_bytes": current.sizes.dg_chain_size_bytes,
            "vro_jwt_size_bytes": current.sizes.vro_jwt_size_bytes,
            "cvc_serialized_size_bytes": current.sizes.cvc_serialized_size_bytes,
            "request_size_bytes": current.sizes.request_size_bytes
        },
        "invariants": {
            "scope_containment_passed": current.invariants.scope_containment_passed,
            "temporal_validity_passed": current.invariants.temporal_validity_passed,
            "signature_verification_passed": current.invariants.signature_verification_passed,
            "chain_integrity_passed": current.invariants.chain_integrity_passed,
            "structural_validity_passed": current.invariants.structural_validity_passed,
            "fail_closed_operation": current.invariants.fail_closed_operation
        },
        "success": current.success,
        "error_code": current.error_code,
        "vro_hash": current.vro_hash,
        "chain_fingerprint": current.chain_fingerprint
    }


@app.post("/verify")
async def verify(request: VerificationRequest) -> Dict[str, Any]:
    """
    Main credential verification endpoint.
    
    Verifies VC-JWT credentials and optionally DG-SD-JWT delegation chains.
    Returns a signed Verification Result Object (VRO) as JWT and metrics.
    """
    # Get metrics collector (if available)
    collector = get_metrics_collector()
    request_id = str(int(time.time() * 1000))
    
    logger.info(f"[REQUEST] Received verification request: request_id={request_id}, policy_id={request.policy_id}")
    logger.info(f"[COLLECTOR] Collector available: {collector is not None}")
    
    try:
        logger.info(
            f"Verification request: policy_id={request.policy_id}, "
            f"has_delegation_chain={bool(request.delegation_chain)}"
        )
        
        # Start metrics collection (server-side)
        # The server always starts its own request to ensure metrics are captured
        if collector:
            logger.info(f"[COLLECTOR] Starting metrics collection for request_id={request_id}")
            profile_hint = request.presentation.type if hasattr(request.presentation, 'type') else "VC-JWT"
            # Always start a new request (clear any previous one first)
            if collector.current is not None:
                # Clear previous request if it exists (shouldn't happen, but safety check)
                logger.warning(f"[METRICS] Clearing previous metrics for request_id={request_id}")
                collector.current = None
            collector.start_request(request_id, "API", profile_hint)
            record_request_size(collector, request.model_dump())
            logger.info(f"[METRICS] Started for request_id={request_id}, profile={profile_hint}")
        else:
            logger.warning(f"[METRICS] Collector is None - metrics will not be captured for request_id={request_id}")
        
        # Load policy
        try:
            policy = load_policy(request.policy_id)
        except PolicyError as e:
            logger.error(f"Policy error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Policy error: {str(e)}")
        
        # Detect profile
        try:
            profile = detect_profile(request.presentation.model_dump())
        except AdapterError as e:
            logger.error(f"Profile detection error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Profile detected - normalization to CVC will handle format differences
        
        # Build CVC (with metrics)
        try:
            if collector:
                collector.record_normalization_start()
                logger.info(f"[METRICS] Normalization STARTED for request_id={request_id}")
            
            cvc = build_cvc(request, policy, profile)
            
            if collector:
                collector.record_normalization_end()
                norm_duration = collector.current.normalization_latency.duration_ms if collector.current else 0
                logger.info(f"[METRICS] Normalization ENDED for request_id={request_id}, duration={norm_duration:.3f}ms")
                record_cvc_size(collector, cvc)
                # Record token sizes
                if profile == "VC-JWT" and hasattr(request.presentation, 'jwt'):
                    record_vc_jwt_size(collector, request.presentation.jwt)
                if request.delegation_chain:
                    record_dg_chain_size(collector, request.delegation_chain)
        except AdapterError as e:
            logger.error(f"CVC construction error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        logger.info(
            f"CVC constructed: issuer={cvc['I_issuer']}, "
            f"subject={cvc['I_subject']}, "
            f"delta_len={len(cvc['Delta'])}"
        )
        
        # Verify CVC (with metrics)
        if collector:
            collector.record_verification_start()
            logger.info(f"[METRICS] Verification STARTED for request_id={request_id}")
        
        success, code, result = verify_cvc(cvc, JWKS_BANK, JWKS_VERIFIER)
        
        if collector:
            collector.record_verification_end()
            verif_duration = collector.current.verification_latency.duration_ms if collector.current else 0
            logger.info(f"[METRICS] Verification ENDED for request_id={request_id}, duration={verif_duration:.3f}ms")
            if success and result.get("vro_jwt"):
                record_vro_size(collector, result["vro_jwt"])
        
        if not success:
            logger.warning(f"Verification failed: code={code}, result={result}")
            if collector:
                collector.record_result(False, code, None, None)
                # Finalize e2e_latency
                collector.current.e2e_latency.stop()
                # Serialize metrics for error response
                metrics = serialize_metrics(collector)
                # HTTPException detail must be a string, so we'll include metrics in a custom response
                error_detail = f"Verification failed: {code}"
            else:
                error_detail = f"Verification failed: {code}"
                metrics = None
            
            # For error responses, we need to return a custom response with metrics
            # instead of raising HTTPException, so the client can still get metrics
            from fastapi.responses import JSONResponse
            error_response = {"detail": error_detail}
            if metrics:
                error_response["metrics"] = metrics
            return JSONResponse(status_code=400, content=error_response)
        
        logger.info("Verification successful")
        
        # Record successful result
        if collector:
            from scripts.metrics_collector import hash_vro
            vro_hash = hash_vro(result["vro_jwt"]) if result.get("vro_jwt") else None
            chain_fingerprint = cvc.get("M", {}).get("chain_fingerprint")
            collector.record_chain_depth(len(cvc.get("Delta", [])))
            collector.record_result(True, "OK", vro_hash, chain_fingerprint)
            # Finalize e2e_latency but keep current for /metrics/current endpoint
            collector.current.e2e_latency.stop()
            e2e_duration = collector.current.e2e_latency.duration_ms if collector.current else 0
            norm_dur = collector.current.normalization_latency.duration_ms if collector.current else 0
            verif_dur = collector.current.verification_latency.duration_ms if collector.current else 0
            logger.info(f"[METRICS] E2E latency STOPPED for request_id={request_id}, duration={e2e_duration:.3f}ms")
            logger.info(f"[METRICS] READY for request_id={request_id}: norm={norm_dur:.3f}ms, verif={verif_dur:.3f}ms, e2e={e2e_duration:.3f}ms")
            # Serialize metrics for response
            metrics = serialize_metrics(collector)
        
        # Return result with metrics included
        response = result.copy()
        if metrics:
            response["metrics"] = metrics
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal error during verification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/verify/oidc4vp")
async def verify_oidc4vp(oidc_response: OIDC4VPResponse) -> Dict[str, str]:
    """
    OIDC4VP verification endpoint.
    
    Receives OIDC4VP authorization response with vp_token,
    extracts Verifiable Presentation, and normalizes to CVC.
    
    Note: This endpoint normalizes the vp_token to standard VerificationRequest
    format. Full OIDC4VP flow (authorization request/response) is not implemented
    in this prototype, but the normalization demonstrates protocol independence.
    """
    try:
        logger.info(f"OIDC4VP verification request: policy_id={oidc_response.policy_id}")
        
        # Normalize OIDC4VP response to standard VerificationRequest
        try:
            normalized_request = normalize_oidc4vp_response(
                oidc_response.vp_token,
                oidc_response.presentation_definition,
                oidc_response.policy_id
            )
        except AdapterError as e:
            logger.error(f"OIDC4VP normalization error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"OIDC4VP normalization error: {str(e)}")
        
        # Create VerificationRequest from normalized data
        request = VerificationRequest(**normalized_request)
        
        # Continue with standard verification flow
        return await verify(request)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OIDC4VP processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"OIDC4VP processing error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8443)
