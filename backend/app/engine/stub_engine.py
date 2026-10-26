"""Pending-Integration Modular Engine Stub for Phase 1.

Complies strictly with the requirement to NEVER fabricate or simulate model output.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from app.models.schemas import (
    EngineStatus,
    EngineMetadata,
    ComparisonResponse,
    ImageQualityDiagnostics,
)
from app.engine.base import FacialEmbeddingEngine


class PendingIntegrationEngine(FacialEmbeddingEngine):
    """Phase 1 baseline engine representing a modular slot ready for model integration."""

    def __init__(self) -> None:
        self._metadata = EngineMetadata(
            engine_id="facecore-stub-v1",
            name="FACECORE Modular Interface (Stub)",
            version="0.1.0-alpha",
            status=EngineStatus.PENDING_INTEGRATION,
            is_mock_data=False,
            description=(
                "Phase 1 modular interface stub. Validates image inputs, calculates image "
                "fidelity diagnostics, and preserves an extensible slot for deep feature "
                "extractors (ArcFace/AdaFace). Does not generate synthetic or fake scores."
            ),
            supported_models=[
                "ArcFace (ResNet-100 / Glint360k) [Planned Step 02]",
                "AdaFace (IR-50 / WebFace4M) [Planned Step 02]",
                "MagFace (ResNet-50) [Planned Step 02]",
            ],
        )

    def get_metadata(self) -> EngineMetadata:
        return self._metadata

    def is_ready(self) -> bool:
        """In Phase 1, model weights are not yet downloaded/loaded."""
        return False

    def extract_features(self, image_bytes: bytes) -> Optional[Any]:
        """Feature extraction is deferred until model weights are mounted."""
        return None

    def compare_faces(
        self,
        image_a_bytes: bytes,
        image_b_bytes: bytes,
        diag_a: ImageQualityDiagnostics,
        diag_b: ImageQualityDiagnostics,
    ) -> ComparisonResponse:
        """Generate response with validated diagnostics while withholding ungrounded scores."""
        now_iso = datetime.now(timezone.utc).isoformat()

        notice = (
            "INFERENCE ENGINE NOT CONFIGURED (PHASE 1 BASELINE): Both Probe (Image A) "
            "and Reference (Image B) passed cryptographic signature and technical quality "
            "validation. However, biometric model inference is not yet integrated. "
            "In accordance with project integrity standards, no simulated or fabricated "
            "similarity percentage is generated. Integration of an authorized embedding "
            "backbone (such as ArcFace or AdaFace) is scheduled for Step 02."
        )

        return ComparisonResponse(
            status="engine_pending_integration",
            timestamp=now_iso,
            engine=self._metadata,
            image_a_diagnostics=diag_a,
            image_b_diagnostics=diag_b,
            similarity_score=None,
            is_match=None,
            interpretation_notice=notice,
        )
