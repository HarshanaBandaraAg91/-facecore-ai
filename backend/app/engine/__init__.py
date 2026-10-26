"""Engine package containing modular interfaces and implementations."""
from .base import FacialEmbeddingEngine
from .stub_engine import PendingIntegrationEngine

__all__ = ["FacialEmbeddingEngine", "PendingIntegrationEngine"]
