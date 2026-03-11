"""
Constitutional Weights Management
Handles the immutable core principles as operational constraints
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from dataclasses import dataclass, field
import firebase_admin
from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot

from config import CONFIG


@dataclass
class Principle:
    """Individual principle with operational constraints"""
    principle_id: str
    name: str
    description: str
    weight: float  # 0-1 influence factor
    hierarchy: int  # Conflict resolution order
    operational_constraint: str  # Code-evaluable constraint
    embedding: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    parent_version: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore-serializable dict"""
        data = {
            "principle_id": self.principle_id,
            "name": self.name,
            "description": self.description,
            "weight": float(self.weight),  # Ensure JSON serializable
            "hierarchy": self.hierarchy,
            "operational_constraint": self.operational_constraint,
            "created_at": self.created_at.isoformat(),
            "version": self.version
        }
        if self.parent_version:
            data["parent_version"] = self.parent_version
        if self.embedding is not None:
            data["embedding"] = self.embedding.tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Principle':
        """Create Principle from Firestore data"""
        principle = cls(
            principle_id=data["principle_id"],
            name=data["name"],
            description=data["description"],
            weight=float(data["weight"]),
            hierarchy=data["hierarchy"],
            operational_constraint=data["operational_constraint"],
            version=data.get("version", 1),
            parent_version=data.get("parent_version")
        )
        
        if "created_at" in data:
            principle.created_at = datetime.fromisoformat(data["created_at"])
        
        if "embedding" in data:
            principle.embedding = np.array(data["embedding"])
        
        return principle


class ConstitutionalWeights:
    """
    Manages the constitutional principles in Firestore
    Provides operational constraint evaluation for Capital Foundry
    """
    
    def __init__(self, firestore_client: Optional[firestore.Client] = None):
        """Initialize with Firestore client"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            try:
                firebase_admin.initialize_app()
            except ValueError as e:
                self.logger.error(f"Firebase initialization failed: {e}")
                raise
        
        self.db = firestore_client or firestore.client()
        self.collection_name = CONFIG.firebase.collections["constitutional_weights"]
        self.collection = self.db.collection(self.collection_name)
        
        # Cache for active principles
        self._active_principles: Optional[List[Principle]] = None
        self._last_update: Optional[datetime] = None
    
    def initialize_constitution(self) -> bool:
        """
        Initialize Firestore with default constitutional principles
        Returns: True if successful
        """
        try:
            # Check if collection exists and has documents
            existing = list(self.collection.limit(1).stream())
            if existing:
                self.logger.info("Constitution already initialized")
                return True
            
            # Create initial principles
            for principle_data in CONFIG.soul_forge.initial_principles:
                principle = Principle(
                    principle_id=principle_data["id"],
                    name=principle_data["name"],
                    description=principle_data["description"],
                    weight=principle_data["weight"],
                    hierarchy=principle_data["hierarchy"],
                    operational_constraint=principle_data["operational_constraint"]
                )
                
                # Add to Firestore
                doc_ref = self.collection.document(principle.principle_id)
                doc_ref.set(principle.to_dict())
            
            self.logger.info(f"Initialized constitution with {len(CONFIG.soul_forge.initial_principles)} principles")
            self._active_principles = None  # Invalidate cache
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize constitution: {e}")
            return False
    
    def get_active_principles(self, force_refresh: bool = False) -> List[Principle]:
        """
        Get all active constitutional principles
        Args:
            force_refresh: Bypass cache and fetch from Firestore
        Returns: List of active principles
        """
        try:
            # Return cached principles if available and not stale
            if (self._active_principles is not None and 
                not force_refresh and
                self._last_update and
                (datetime.utcnow() - self._last_update).seconds < 300):  # 5 minute cache
                return self._active_principles
            
            # Fetch from Firestore
            principles = []
            docs = self.collection.stream()
            
            for doc in docs:
                try:
                    principle = Principle.from_dict(doc.to_dict())
                    principles.append(principle)
                except (KeyError, ValueError) as e:
                    self.logger.warning(f"Failed to parse principle {doc.id}: {e}")
            
            # Sort by hierarchy (ascending)
            principles.sort(key=lambda p: p.hierarchy)
            
            # Update cache
            self._active_principles = principles
            self._last_update = datetime.utcnow()
            
            self.logger.debug(f"Retrieved {len(principles)} active principles")
            return principles
            
        except Exception as e:
            self.logger.error(f"Failed to fetch active principles: {e}")
            # Return empty list on error
            return []
    
    def evaluate_action_alignment(self, 
                                 action_vector: np.ndarray,
                                 action_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate how well an action aligns with constitutional principles
        Args:
            action_vector: Numerical representation of proposed action
            action_context: Context dict with market state, risk metrics, etc.
        Returns: Dict with alignment scores and any constraint violations
        """
        principles = self.get_active_principles()
        
        if not principles:
            self.logger.warning("No principles available for alignment evaluation")
            return {
                "overall_alignment": 0.0,
                "violations": [],
                "passed": False
            }
        
        scores = []
        violations = []
        
        for principle in principles:
            try:
                # Calculate alignment for this principle
                # Simple initial implementation: weight * random alignment
                # TODO: Replace with actual semantic/operational alignment calculation
                alignment_score = principle.weight * np.random.uniform(0.7, 1.0)
                scores.append(alignment_score)
                
                # Check operational constraint
                constraint_met = self._evaluate_constraint(