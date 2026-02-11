"""
Federated Learning + Blockchain API Routes

FastAPI routes for:
- Federation coordination (round management, gradient submission)
- Blockchain ledger queries (block retrieval, provenance tracking)
- Privacy configuration (DP budget, encryption)
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import numpy as np

from backend.core.fl_blockchain import (
    get_federation_orchestrator,
    get_blockchain_ledger,
    FLBlockchainConfig,
    get_fl_config,
    TrainingRoundState,
)
from backend.core.fl_blockchain.utils import get_privacy_metrics, get_model_metrics

logger = logging.getLogger("jarvis.api.fl_blockchain")

# Create router
router = APIRouter(prefix="/api/fl-blockchain", tags=["federated-learning"])


# ==================== Pydantic Models ====================

class OrganizationRegistration(BaseModel):
    """Organization registration request"""
    org_id: str = Field(..., description="Unique organization ID")
    public_key: str = Field(..., description="Public key for signature verification")
    endpoint: str = Field(..., description="Organization's API endpoint")
    capabilities: Dict[str, bool] = Field(
        default_factory=lambda: {
            "federated_tgnn": True,
            "federated_rl": True,
        },
        description="Organization capabilities"
    )


class GradientSubmission(BaseModel):
    """Gradient submission from organization"""
    round_id: int = Field(..., description="Training round ID")
    org_id: str = Field(..., description="Submitting organization")
    gradient_hash: str = Field(..., description="SHA-256 hash of encrypted gradient")
    encrypted_gradient: str = Field(..., description="Base64-encoded encrypted gradient")
    signature: str = Field(..., description="HMAC signature")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class AggregationRequest(BaseModel):
    """Request to aggregate gradients"""
    round_id: int = Field(..., description="Training round ID")
    decrypted_gradients: Dict[str, str] = Field(
        ...,
        description="org_id → base64-encoded decrypted gradient"
    )
    sample_counts: Dict[str, int] = Field(..., description="org_id → number of samples")


class RoundStartRequest(BaseModel):
    """Request to start training round"""
    round_number: Optional[int] = Field(None, description="Round number (auto if None)")


class BlockchainVerificationRequest(BaseModel):
    """Request to verify model on blockchain"""
    model_hash: str = Field(..., description="Model hash to verify")
    org_signatures: Dict[str, str] = Field(..., description="org_id → signature")
    round_number: int = Field(..., description="Training round number")


# ==================== Federation Routes ====================

@router.post("/federation/register")
async def register_organization(org: OrganizationRegistration) -> Dict[str, Any]:
    """
    Register new organization for federation
    
    Returns:
        Registration confirmation with token and config
    """
    try:
        orchestrator = get_federation_orchestrator()
        result = orchestrator.register_organization(
            org_id=org.org_id,
            public_key=org.public_key,
            endpoint=org.endpoint,
            capabilities=org.capabilities,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Organization registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/federation/organizations")
async def list_organizations() -> Dict[str, Any]:
    """Get list of registered organizations"""
    try:
        orchestrator = get_federation_orchestrator()
        org_ids = orchestrator.get_registered_organizations()
        return {
            "status": "success",
            "organizations": org_ids,
            "count": len(org_ids),
        }
    except Exception as e:
        logger.error(f"Failed to list organizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/federation/round/start")
async def start_training_round(req: RoundStartRequest) -> Dict[str, Any]:
    """
    Start new federated training round
    
    Returns:
        Round information (ID, deadline, privacy params, global model hash)
    """
    try:
        orchestrator = get_federation_orchestrator()
        result = orchestrator.start_training_round(req.round_number)
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Failed to start training round: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/federation/round/submit-gradient")
async def submit_gradient(sub: GradientSubmission) -> Dict[str, Any]:
    """
    Submit encrypted gradient for round
    
    Returns:
        Submission acknowledgment
    """
    try:
        orchestrator = get_federation_orchestrator()
        result = orchestrator.submit_gradient(
            round_number=sub.round_id,
            org_id=sub.org_id,
            gradient_hash=sub.gradient_hash,
            encrypted_gradient=sub.encrypted_gradient,
            signature=sub.signature,
            metadata=sub.metadata,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Gradient submission failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/federation/round/{round_id}/status")
async def get_round_status(round_id: int) -> Dict[str, Any]:
    """Get status of specific training round"""
    try:
        orchestrator = get_federation_orchestrator()
        status = orchestrator.get_round_status(round_id)
        return {
            "status": "success",
            "round": status,
        }
    except Exception as e:
        logger.error(f"Failed to get round status: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/federation/status")
async def get_federation_status() -> Dict[str, Any]:
    """Get overall federation status"""
    try:
        orchestrator = get_federation_orchestrator()
        status = orchestrator.get_federation_status()
        return {
            "status": "success",
            "federation": status,
        }
    except Exception as e:
        logger.error(f"Failed to get federation status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Blockchain Routes ====================

@router.get("/blockchain/ledger/blocks")
async def get_blocks(
    from_height: int = 0,
    to_height: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get blocks from blockchain ledger
    
    Args:
        from_height: Start block height
        to_height: End block height (inclusive)
    
    Returns:
        List of blocks
    """
    try:
        ledger = get_blockchain_ledger()
        blocks = ledger.get_blocks(from_height, to_height)
        block_dicts = [b.to_dict() for b in blocks]
        
        return {
            "status": "success",
            "blocks": block_dicts,
            "count": len(block_dicts),
        }
    except Exception as e:
        logger.error(f"Failed to get blocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blockchain/ledger/block/{height}")
async def get_block(height: int) -> Dict[str, Any]:
    """Get specific block by height"""
    try:
        ledger = get_blockchain_ledger()
        block = ledger.get_block(height)
        
        if not block:
            raise HTTPException(status_code=404, detail=f"Block {height} not found")
        
        return {
            "status": "success",
            "block": block.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get block {height}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blockchain/ledger/verify")
async def verify_ledger() -> Dict[str, Any]:
    """Verify blockchain ledger integrity"""
    try:
        ledger = get_blockchain_ledger()
        is_valid, error = ledger.verify_chain()
        
        return {
            "status": "success",
            "valid": is_valid,
            "error": error if not is_valid else None,
            "chain_length": ledger.get_chain_length(),
        }
    except Exception as e:
        logger.error(f"Ledger verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blockchain/provenance/{model_hash}")
async def get_model_provenance(model_hash: str) -> Dict[str, Any]:
    """
    Get lineage (provenance) for a model
    
    Args:
        model_hash: Model hash to trace
    
    Returns:
        List of blocks in model's lineage
    """
    try:
        ledger = get_blockchain_ledger()
        lineage = ledger.get_model_lineage(model_hash)
        
        return {
            "status": "success",
            "model_hash": model_hash,
            "lineage": lineage,
            "depth": len(lineage),
        }
    except Exception as e:
        logger.error(f"Failed to get provenance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Privacy Routes ====================

@router.get("/privacy/config")
async def get_privacy_config() -> Dict[str, Any]:
    """Get current privacy configuration"""
    try:
        config = get_fl_config()
        metrics = get_privacy_metrics(
            epsilon=config.privacy.epsilon,
            delta=config.privacy.delta,
            clipping_norm=config.privacy.clipping_norm,
        )
        
        return {
            "status": "success",
            "privacy": {
                "epsilon": config.privacy.epsilon,
                "delta": config.privacy.delta,
                "clipping_norm": config.privacy.clipping_norm,
                "homomorphic_encryption_enabled": config.privacy.enable_homomorphic_encryption,
                "secure_aggregation_enabled": config.privacy.enable_secure_aggregation,
                "metrics": metrics,
            }
        }
    except Exception as e:
        logger.error(f"Failed to get privacy config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/privacy/budget")
async def get_privacy_budget() -> Dict[str, Any]:
    """Get privacy budget status"""
    try:
        # In production: track actual budget consumption
        config = get_fl_config()
        
        return {
            "status": "success",
            "budget": {
                "max_epsilon": 10.0,
                "used_epsilon": 2.0,
                "remaining_epsilon": 8.0,
                "max_delta": 0.01,
                "used_delta": 0.001,
                "remaining_delta": 0.009,
            }
        }
    except Exception as e:
        logger.error(f"Failed to get privacy budget: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health & Info Routes ====================

@router.get("/health")
async def fl_blockchain_health() -> Dict[str, Any]:
    """Check FL+Blockchain service health"""
    try:
        orchestrator = get_federation_orchestrator()
        ledger = get_blockchain_ledger()
        config = get_fl_config()
        
        fed_status = orchestrator.get_federation_status()
        ledger_valid, _ = ledger.verify_chain()
        
        return {
            "status": "healthy",
            "service": "fl-blockchain",
            "federation": {
                "active": True,
                "current_round": fed_status["current_round"],
                "organizations": fed_status["stats"]["total_organizations"],
            },
            "blockchain": {
                "valid": ledger_valid,
                "chain_length": ledger.get_chain_length(),
            },
            "privacy": {
                "dp_enabled": True,
                "he_enabled": config.privacy.enable_homomorphic_encryption,
                "secagg_enabled": config.privacy.enable_secure_aggregation,
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def fl_blockchain_info() -> Dict[str, Any]:
    """Get FL+Blockchain system information"""
    try:
        config = get_fl_config()
        
        return {
            "status": "success",
            "service": "Federated Learning + Blockchain XDR",
            "version": "1.0.0",
            "components": {
                "federation_orchestrator": "Production",
                "privacy_layer": "DP + HE + Sanitization",
                "blockchain_ledger": "Immutable",
                "federated_models": "TGNN + RL",
            },
            "configuration": {
                "aggregation_method": config.aggregation.method,
                "privacy_epsilon": config.privacy.epsilon,
                "privacy_delta": config.privacy.delta,
                "min_clients_per_round": config.aggregation.min_clients_per_round,
                "blockchain_block_interval": config.blockchain.create_block_every_n_rounds,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
