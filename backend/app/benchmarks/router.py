"""FastAPI router endpoints for benchmark dataset discovery, execution, and reporting."""

from typing import List
from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from app.benchmarks.schemas import (
    DatasetMetadata,
    BenchmarkRunConfig,
    BenchmarkResult,
    BenchmarkRunSummary,
)
from app.benchmarks.manifest import DATASETS_REGISTRY, sync_dataset_registry_with_disk
from app.benchmarks.dataset_installer import (
    get_dataset_install_status,
    install_lfw_dataset,
)
from app.benchmarks.runner import (
    benchmark_runner,
    get_all_runs_summary,
    get_run_by_id,
    get_pairwise_details,
)
from app.benchmarks.metrics import (
    export_benchmark_json,
    export_pairwise_csv,
    export_benchmark_markdown,
)

router = APIRouter(prefix="/api/benchmarks", tags=["Model Benchmarks"])


@router.get("/datasets", response_model=List[DatasetMetadata])
async def list_datasets() -> List[DatasetMetadata]:
    """Retrieve all registered evaluation datasets and their availability/verification status."""
    sync_dataset_registry_with_disk()
    return list(DATASETS_REGISTRY.values())


@router.get("/datasets/{dataset_id}/status")
async def get_dataset_status_endpoint(dataset_id: str):
    """Retrieve detailed archive installation and integrity verification state."""
    sync_dataset_registry_with_disk()
    meta = DATASETS_REGISTRY.get(dataset_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )
    return get_dataset_install_status(dataset_id)


@router.post("/datasets/{dataset_id}/install")
async def install_dataset_endpoint(dataset_id: str):
    """Trigger verified local installation of an authorized research dataset."""
    if dataset_id != "lfw-canonical-v1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Automated installation is currently only supported for 'lfw-canonical-v1'.",
        )
    res = install_lfw_dataset()
    sync_dataset_registry_with_disk()
    return res


@router.get("/history", response_model=List[BenchmarkRunSummary])
async def list_benchmark_history() -> List[BenchmarkRunSummary]:
    """Retrieve run summaries of all recorded evaluation experiments."""
    return get_all_runs_summary()


@router.get("/runs/{run_id}", response_model=BenchmarkResult)
async def get_benchmark_run(run_id: str) -> BenchmarkResult:
    """Retrieve comprehensive telemetry, ROC curves, and confusion matrix for a specific run."""
    run = get_run_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark run '{run_id}' not found in registry.",
        )
    return run


@router.post("/run", response_model=BenchmarkResult)
async def execute_benchmark_run(config: BenchmarkRunConfig) -> BenchmarkResult:
    """Trigger a scientific evaluation run of the active SFace model against a dataset."""
    try:
        return benchmark_runner.run_benchmark(config)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(ve),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark execution failed: {str(exc)}",
        )


@router.get("/runs/{run_id}/export/json")
async def export_run_json(run_id: str):
    """Download full experiment metrics and ROC points as structured JSON."""
    run = get_run_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark run '{run_id}' not found.",
        )
    json_str = export_benchmark_json(run)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="facecore_benchmark_{run_id}.json"'
        },
    )


@router.get("/runs/{run_id}/export/csv")
async def export_run_csv(run_id: str):
    """Download detailed pairwise classification evaluation data as CSV."""
    run = get_run_by_id(run_id)
    details = get_pairwise_details(run_id)
    if not run or not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark run '{run_id}' not found or pairwise details missing.",
        )

    csv_str = export_pairwise_csv(
        pair_ids=details["pair_ids"],
        identities_a=details["identities_a"],
        identities_b=details["identities_b"],
        is_genuine_list=details["labels"],
        similarity_scores=details["scores"],
        threshold=details["optimal_threshold"],
    )

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="facecore_pairs_{run_id}.csv"'
        },
    )


@router.get("/runs/{run_id}/export/markdown")
async def export_run_markdown(run_id: str):
    """Download full scientific audit report as Markdown."""
    run = get_run_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark run '{run_id}' not found.",
        )
    md_str = export_benchmark_markdown(run)
    return Response(
        content=md_str,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="facecore_benchmark_{run_id}.md"'
        },
    )
