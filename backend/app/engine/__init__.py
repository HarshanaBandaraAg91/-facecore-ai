"""Engine package containing modular interfaces and neural implementations."""
from .base import FacialEmbeddingEngine
from .stub_engine import PendingIntegrationEngine
from .real_engine import (
    RealFacialEmbeddingEngine,
    compute_cosine_similarity,
    calculate_display_score,
    NoFaceDetectedError,
    MultipleFacesDetectedError,
    ModelNotReadyError,
    InvalidEmbeddingError,
)

__all__ = [
    "FacialEmbeddingEngine",
    "PendingIntegrationEngine",
    "RealFacialEmbeddingEngine",
    "compute_cosine_similarity",
    "calculate_display_score",
    "NoFaceDetectedError",
    "MultipleFacesDetectedError",
    "ModelNotReadyError",
    "InvalidEmbeddingError",
]
