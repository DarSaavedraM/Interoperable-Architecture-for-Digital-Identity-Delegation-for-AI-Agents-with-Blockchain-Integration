"""
Blockchain anchor abstraction for delegation chain anchoring.

This module provides a mock blockchain implementation for prototype purposes.
In production, this would connect to a real blockchain (Ethereum, Hyperledger, etc.).
"""

import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AnchorError(Exception):
    """Exception for anchor-related errors."""
    pass


class BlockchainAnchor(ABC):
    """
    Abstract base class for blockchain anchor implementations.
    
    This allows the system to work with different blockchain backends:
    - MockBlockchainAnchor: For prototype/testing (in-memory/JSON)
    - EthereumAnchor: For Ethereum-based anchoring (future)
    - HyperledgerAnchor: For Hyperledger-based anchoring (future)
    """
    
    @abstractmethod
    def anchor_chain_fingerprint(
        self, 
        fingerprint: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Anchor a chain fingerprint to the blockchain.
        
        Args:
            fingerprint: SHA256 hash of the delegation chain
            metadata: Optional metadata (timestamp, issuer, etc.)
            
        Returns:
            Dict with anchor proof containing:
            - block_hash: Hash of the block containing the anchor
            - block_number: Block number (or sequence number for mock)
            - transaction_hash: Transaction hash (or anchor ID for mock)
            - timestamp: Timestamp of anchoring
            - proof: Cryptographic proof of anchoring
        """
        pass
    
    @abstractmethod
    def verify_anchor(
        self, 
        fingerprint: str, 
        anchor_proof: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify that a chain fingerprint is anchored.
        
        Args:
            fingerprint: SHA256 hash of the delegation chain
            anchor_proof: Optional anchor proof (if None, will look it up)
            
        Returns:
            Tuple (is_anchored, error_message)
        """
        pass
    
    @abstractmethod
    def get_anchor_proof(
        self, 
        fingerprint: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve anchor proof for a given fingerprint.
        
        Args:
            fingerprint: SHA256 hash of the delegation chain
            
        Returns:
            Anchor proof dict or None if not found
        """
        pass


class MockBlockchainAnchor(BlockchainAnchor):
    """
    Mock blockchain anchor implementation for prototype.
    
    Stores anchors in a JSON file (simulating blockchain storage).
    Uses a hash chain for integrity verification.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize mock blockchain anchor.
        
        Args:
            storage_path: Path to JSON file for storing anchors.
                         If None, uses in-memory storage only.
        """
        self.storage_path = storage_path
        self._in_memory_anchors: Dict[str, Dict[str, Any]] = {}
        self._chain: list = []  # Hash chain for integrity
        self._load_from_storage()
    
    def _load_from_storage(self) -> None:
        """Load anchors from storage file if it exists."""
        if self.storage_path and self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self._in_memory_anchors = data.get("anchors", {})
                self._chain = data.get("chain", [])
                logger.info(f"Loaded {len(self._in_memory_anchors)} anchors from {self.storage_path}")
            except Exception as e:
                logger.warning(f"Could not load anchors from {self.storage_path}: {e}")
                self._in_memory_anchors = {}
                self._chain = []
    
    def _save_to_storage(self) -> None:
        """Save anchors to storage file."""
        if self.storage_path:
            try:
                data = {
                    "anchors": self._in_memory_anchors,
                    "chain": self._chain,
                    "last_updated": time.time()
                }
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                self.storage_path.write_text(json.dumps(data, indent=2, sort_keys=True))
            except Exception as e:
                logger.warning(f"Could not save anchors to {self.storage_path}: {e}")
    
    def anchor_chain_fingerprint(
        self, 
        fingerprint: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Anchor a chain fingerprint (mock implementation)."""
        if not fingerprint:
            raise AnchorError("Fingerprint cannot be empty")
        
        # Check if already anchored
        if fingerprint in self._in_memory_anchors:
            existing = self._in_memory_anchors[fingerprint]
            logger.debug(f"Fingerprint {fingerprint[:16]}... already anchored at block {existing.get('block_number')}")
            return existing
        
        # Create new anchor entry
        block_number = len(self._chain) + 1
        timestamp = int(time.time())
        
        # Build block data
        block_data = {
            "fingerprint": fingerprint,
            "metadata": metadata or {},
            "timestamp": timestamp,
            "block_number": block_number
        }
        
        # Calculate block hash (simulating blockchain block)
        block_hash_input = json.dumps(block_data, sort_keys=True).encode()
        if self._chain:
            # Chain to previous block (hash chain)
            previous_hash = self._chain[-1].get("block_hash", "")
            block_hash_input += previous_hash.encode()
        
        block_hash = hashlib.sha256(block_hash_input).hexdigest()
        
        # Create transaction hash (simulating transaction ID)
        tx_data = f"{fingerprint}{timestamp}{block_number}".encode()
        transaction_hash = hashlib.sha256(tx_data).hexdigest()
        
        # Create anchor proof
        anchor_proof = {
            "block_hash": block_hash,
            "block_number": block_number,
            "transaction_hash": transaction_hash,
            "timestamp": timestamp,
            "proof": {
                "type": "mock_blockchain",
                "fingerprint": fingerprint,
                "block_hash": block_hash,
                "chain_position": block_number
            }
        }
        
        # Store anchor
        self._in_memory_anchors[fingerprint] = anchor_proof
        
        # Add to chain
        self._chain.append({
            "block_hash": block_hash,
            "block_number": block_number,
            "fingerprint": fingerprint,
            "timestamp": timestamp
        })
        
        # Save to storage
        self._save_to_storage()
        
        logger.info(
            f"Anchored fingerprint {fingerprint[:16]}... at block {block_number} "
            f"(tx: {transaction_hash[:16]}...)"
        )
        
        return anchor_proof
    
    def verify_anchor(
        self, 
        fingerprint: str, 
        anchor_proof: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Verify that a chain fingerprint is anchored."""
        if not fingerprint:
            return False, "Fingerprint cannot be empty"
        
        # If proof provided, verify it
        if anchor_proof:
            proof_fingerprint = anchor_proof.get("proof", {}).get("fingerprint")
            if proof_fingerprint != fingerprint:
                return False, "Anchor proof fingerprint mismatch"
            
            # Verify proof is in our storage
            if fingerprint not in self._in_memory_anchors:
                return False, "Anchor proof not found in storage"
            
            stored = self._in_memory_anchors[fingerprint]
            if stored.get("transaction_hash") != anchor_proof.get("transaction_hash"):
                return False, "Anchor proof transaction hash mismatch"
        
        # Check if anchored
        if fingerprint not in self._in_memory_anchors:
            return False, "Fingerprint not anchored"
        
        # Verify chain integrity (optional but recommended)
        stored_proof = self._in_memory_anchors[fingerprint]
        block_number = stored_proof.get("block_number")
        
        if block_number and block_number <= len(self._chain):
            chain_entry = self._chain[block_number - 1]
            if chain_entry.get("fingerprint") != fingerprint:
                return False, "Chain integrity verification failed"
        
        return True, None
    
    def get_anchor_proof(
        self, 
        fingerprint: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve anchor proof for a given fingerprint."""
        return self._in_memory_anchors.get(fingerprint)


# Global anchor instance (lazy initialization)
_anchor_instance: Optional[BlockchainAnchor] = None


def get_anchor_instance(force_mock: bool = False) -> Optional[BlockchainAnchor]:
    """
    Get the global anchor instance.
    
    Args:
        force_mock: If True, always return MockBlockchainAnchor even if configured otherwise
        
    Returns:
        BlockchainAnchor instance or None if anchoring is disabled
    """
    global _anchor_instance
    return _anchor_instance


def set_anchor_instance(anchor: Optional[BlockchainAnchor]) -> None:
    """
    Set the global anchor instance (for testing).
    
    Args:
        anchor: BlockchainAnchor instance or None to disable
    """
    global _anchor_instance
    _anchor_instance = anchor


def create_mock_anchor(storage_path: Optional[Path] = None) -> MockBlockchainAnchor:
    """
    Create a new MockBlockchainAnchor instance.
    
    Args:
        storage_path: Optional path to JSON storage file
        
    Returns:
        MockBlockchainAnchor instance
    """
    return MockBlockchainAnchor(storage_path=storage_path)


