"""Abstract base interface for facial embedding and verification engines.

This modular contract ensures that real neural embedding backbones (e.g. ArcFace,
AdaFace, FaceNet) can be plugged in during Phase 2 without modifying API routes
or user interface code.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from app.models.schemas import (
    EngineMetadata,
    ComparisonResponse,
    ImageQualityDiagnostics,
)


class FacialEmbeddingEngine(ABC):
    """Abstract interface defining required capabilities for any biometric engine."""

    @abstractmethod
    def get_metadata(self) -> EngineMetadata:
        """Return engine metadata, active model name, version, and integration status."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True if a neural network model is loaded and ready to infer embeddings."""
        pass

    @abstractmethod
    def extract_features(self, image_bytes: bytes) -> Optional[Any]:
        """Extract a fixed-dimension vector embedding (e.g. 512-d float array).

        Returns None if engine is pending integration or face is not detected.
        """
        pass

    @abstractmethod
    def compare_faces(
        self,
        image_a_bytes: bytes,
        image_b_bytes: bytes,
        diag_a: ImageQualityDiagnostics,
        diag_b: ImageQualityDiagnostics,
    ) -> ComparisonResponse:
        """Run facial comparison between Probe (A) and Reference (B) images.

        In accordance with scientific integrity rules, this method MUST NOT
        fabricate scores, simulate percentages, or return fake verdicts
        when an authentic embedding model is not yet integrated.
        """
        pass
