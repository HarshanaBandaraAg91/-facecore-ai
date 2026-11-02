"""Pydantic schemas for the model benchmarking and evaluation framework."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DatasetStatus(str, Enum):
    UNRUN = "UNRUN"
    DATASET_VERIFIED = "DATASET_VERIFIED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DatasetMetadata(BaseModel):
    dataset_id: str = Field(..., description="Unique slug for the benchmark dataset")
    name: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Detailed description and focus")
    total_images: int = Field(..., description="Total images in full corpus")
    total_identities: int = Field(..., description="Total unique identities")
    total_pairs: int = Field(..., description="Total pairs in evaluation protocol")
    verification_status: DatasetStatus = Field(DatasetStatus.UNRUN, description="Benchmark run state")
    is_available: bool = Field(False, description="Whether dataset files or fixtures are verified locally")
    license: str = Field(..., description="Dataset usage license terms")
    source_url: str = Field(..., description="Official academic/research source URL")
    local_path: Optional[str] = Field(None, description="Local verified path if present")
    dataset_type: Optional[str] = Field("real", description="'real' photograph dataset or 'synthetic' fixture")
    installation_status: Optional[str] = Field("NOT_INSTALLED", description="Installation status: NOT_INSTALLED, VERIFIED, etc.")


class PairAnnotation(BaseModel):
    pair_id: str = Field(..., description="Unique identifier for evaluation pair")
    image_a: str = Field(..., description="Path, relative reference, or identifier for probe image")
    image_b: str = Field(..., description="Path, relative reference, or identifier for reference image")
    is_genuine: bool = Field(..., description="True if same person (genuine), False if impostor")
    identity_a: str = Field(..., description="Subject identity string for image A")
    identity_b: str = Field(..., description="Subject identity string for image B")
    fold_index: Optional[int] = Field(0, description="K-fold partition index [0-9]")
    condition: str = Field("baseline", description="Evaluation perturbation condition")


class BenchmarkRunConfig(BaseModel):
    dataset_id: str = Field("lfw-canonical-v1", description="ID of dataset to benchmark")
    evaluate_robustness: bool = Field(True, description="Whether to execute controlled perturbation suite")
    max_pairs: Optional[int] = Field(None, description="Optional cap on evaluation pairs for quick profiling")
    random_seed: int = Field(42, description="Deterministic random seed for reproducibility")
    face_selection_policy: str = Field("center_face", description="Acquisition policy: 'center_face' or 'strict_single_face'")
    transfer_threshold: Optional[float] = Field(None, description="Optional transferred threshold (e.g. from LFW) to evaluate generalization")
    description: Optional[str] = Field(None, description="Optional user note for run")


class ROCCurvePoint(BaseModel):
    threshold: float
    far: float
    frr: float
    tar: float
    precision: float
    recall: float


class TARAtFAR(BaseModel):
    far_target: float = Field(..., description="Target FAR operating point (e.g. 0.01 = 1%)")
    tar: float = Field(..., description="Empirical True Acceptance Rate achieved")
    threshold: float = Field(..., description="Decision threshold calibrated for target FAR")
    observed_far: Optional[float] = Field(None, description="Actual observed empirical FAR")
    false_accept_count: Optional[int] = Field(None, description="Count of impostor pairs falsely accepted")
    total_impostors: Optional[int] = Field(None, description="Total impostor pairs in evaluation")
    is_statistically_valid: Optional[bool] = Field(True, description="True if sample size >= 1/FAR_target")
    rule_of_three_valid: Optional[bool] = Field(True, description="True if sample size >= 3/FAR_target")
    sample_size_advisory: Optional[str] = Field(None, description="Advisory on sample size uncertainty")


class ConfusionMatrix(BaseModel):
    tp: int = Field(..., description="True Positives (Genuine matched as Genuine)")
    fp: int = Field(..., description="False Positives (Impostor matched as Genuine)")
    tn: int = Field(..., description="True Negatives (Impostor rejected as Impostor)")
    fn: int = Field(..., description="False Negatives (Genuine rejected as Impostor)")
    accuracy: float = Field(..., description="(TP + TN) / Total")
    precision: float = Field(..., description="TP / (TP + FP)")
    recall: float = Field(..., description="TP / (TP + FN)")
    f1_score: float = Field(..., description="2 * Precision * Recall / (Precision + Recall)")


class ConfidenceInterval(BaseModel):
    metric: str = Field(..., description="Metric name (e.g. 'EER', 'ROC-AUC', 'Accuracy')")
    mean: float = Field(..., description="Observed point estimate")
    ci_lower: float = Field(..., description="Lower 95% bootstrap bound")
    ci_upper: float = Field(..., description="Upper 95% bootstrap bound")
    confidence_level: float = Field(0.95, description="Confidence level (default 0.95)")


class RobustnessConditionResult(BaseModel):
    condition_name: str = Field(..., description="Perturbation name (e.g. 'Gaussian Blur (Light)')")
    description: str = Field(..., description="Implementation details")
    sample_size: int = Field(..., description="Number of pairs evaluated under this condition")
    accuracy: float = Field(..., description="Accuracy at reference threshold")
    eer: float = Field(..., description="Equal Error Rate under this condition")
    auc: float = Field(..., description="ROC-AUC under this condition")
    tar_at_far_01: float = Field(..., description="TAR at FAR=1% under this condition")
    attempted_pairs: Optional[int] = Field(None, description="Total attempted pairs for condition")
    successful_pairs: Optional[int] = Field(None, description="Successfully acquired and evaluated pairs")
    failed_pairs: Optional[int] = Field(None, description="Failed detection or extraction pairs")
    fta_rate: Optional[float] = Field(None, description="Failure to Acquire rate under perturbation")
    genuine_mean: Optional[float] = Field(None, description="Mean genuine cosine similarity")
    impostor_mean: Optional[float] = Field(None, description="Mean impostor cosine similarity")
    far_at_baseline_thresh: Optional[float] = Field(None, description="FAR observed at baseline threshold")
    frr_at_baseline_thresh: Optional[float] = Field(None, description="FRR observed at baseline threshold")


class FTABreakdown(BaseModel):
    no_face_detected: int = Field(0, description="Pairs failed due to 0 faces detected in either image")
    multiple_faces_detected: int = Field(0, description="Pairs failed due to >1 faces detected without selection")
    alignment_failed: int = Field(0, description="Pairs failed due to landmark or alignment failure")
    inference_error: int = Field(0, description="Pairs failed due to model inference failure")


class BenchmarkResult(BaseModel):
    run_id: str = Field(..., description="Unique UUID for evaluation run")
    dataset_id: str = Field(..., description="Target dataset slug")
    dataset_name: str = Field(..., description="Dataset display title")
    model_name: str = Field("SFace (SphereFace2)", description="Evaluated embedding model")
    model_version: str = Field("2021dec-2023mar", description="Evaluated model version")
    timestamp: str = Field(..., description="ISO 8601 evaluation timestamp")
    status: DatasetStatus = Field(DatasetStatus.COMPLETED, description="Run execution status")
    
    total_pairs: int = Field(..., description="Total pairs evaluated")
    genuine_pairs: int = Field(..., description="Count of genuine pairs")
    impostor_pairs: int = Field(..., description="Count of impostor pairs")
    
    eer: float = Field(..., description="Equal Error Rate [0.0 - 1.0]")
    eer_threshold: float = Field(..., description="Threshold at EER operating point")
    auc: float = Field(..., description="Area Under ROC Curve [0.0 - 1.0]")
    optimal_threshold: float = Field(..., description="Threshold optimizing cross-validation accuracy")
    accuracy: float = Field(..., description="Classification accuracy at optimal threshold")
    
    confidence_intervals: List[ConfidenceInterval] = Field(default_factory=list)
    confusion_matrix: ConfusionMatrix
    tar_at_far_table: List[TARAtFAR] = Field(default_factory=list)
    roc_curve: List[ROCCurvePoint] = Field(default_factory=list)
    far_frr_curve: List[ROCCurvePoint] = Field(default_factory=list)
    robustness_results: List[RobustnessConditionResult] = Field(default_factory=list)
    
    execution_time_seconds: float = Field(..., description="Wall clock evaluation duration in seconds")
    error_message: Optional[str] = Field(None, description="Error reason if run failed")

    # Audit & Scientific Provenance Metadata (Step 06)
    dataset_manifest_hash: Optional[str] = Field(None, description="SHA-256 fingerprint of evaluation pair manifest")
    model_weights_hash: Optional[str] = Field(None, description="SHA-256 fingerprint of active model weights")
    system_environment: Optional[Dict[str, str]] = Field(None, description="Host and library runtime environment versions")
    evaluation_protocol: Optional[str] = Field(None, description="Formal evaluation protocol specification")
    total_requested_pairs: Optional[int] = Field(None, description="Total requested evaluation pairs before FTA")
    failure_to_acquire_count: Optional[int] = Field(0, description="Count of pairs failing detection/extraction")
    failure_to_acquire_rate: Optional[float] = Field(0.0, description="Failure to Acquire (FTA) rate")
    fta_breakdown: Optional[FTABreakdown] = Field(default_factory=FTABreakdown, description="Categorized FTA breakdown per ISO/IEC 19795-1")
    is_real_photographs: bool = Field(False, description="True if run evaluated real photographs from research datasets, False if synthetic fixture")
    bootstrap_method: Optional[str] = Field(None, description="Bootstrap resampling methodology")
    
    # Cross-Dataset Generalization & Threshold Transfer (Step 08)
    transferred_threshold: Optional[float] = Field(None, description="Transferred baseline threshold (e.g. from LFW)")
    transferred_threshold_source: Optional[str] = Field(None, description="Provenance of transferred threshold")
    transferred_accuracy: Optional[float] = Field(None, description="Accuracy under transferred threshold without native tuning")
    transferred_confusion_matrix: Optional[ConfusionMatrix] = Field(None, description="Confusion matrix under transferred threshold")
    cross_dataset_condition: Optional[str] = Field(None, description="Evaluated challenge domain: cross_pose, cross_age, frontal, etc.")

    # Scientific Validation, Full Evaluation & Reproducibility (Step 09)
    yunet_weights_hash: Optional[str] = Field(None, description="SHA-256 fingerprint of YuNet detector ONNX model")
    sface_weights_hash: Optional[str] = Field(None, description="SHA-256 fingerprint of SFace feature extractor ONNX model")
    pair_list_hash: Optional[str] = Field(None, description="SHA-256 fingerprint of the pair protocol definition file")
    reproducibility_command: Optional[str] = Field(None, description="Command to reproduce benchmark run exactly")
    official_total_pairs: Optional[int] = Field(None, description="Total pairs in the official benchmark protocol")
    resolved_pairs_count: Optional[int] = Field(None, description="Pairs whose image files exist locally on disk")
    unresolved_pairs_count: Optional[int] = Field(None, description="Pairs with missing image files on local disk")
    missing_images_count: Optional[int] = Field(None, description="Unique missing image files on disk")
    evaluation_completeness: Optional[str] = Field(None, description="'COMPLETE_OFFICIAL_CORPUS' or 'VERIFIED_LOCAL_SUBSET'")
    metric_calculation_version: Optional[str] = Field("step09-audit-v1", description="Audit version for metric calculations")


class BenchmarkRunSummary(BaseModel):
    run_id: str
    dataset_id: str
    dataset_name: str
    timestamp: str
    status: DatasetStatus
    total_pairs: int
    eer: float
    auc: float
    accuracy: float
    execution_time_seconds: float
