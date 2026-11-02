"""SQLite database connection and audit persistence service for FACECORE AI.

Adheres strictly to biometric privacy & security:
- NEVER persists uploaded face images or binary payloads.
- NEVER persists extracted 128-d neural embeddings.
- Stores only cryptographic SHA-256 hash prefixes, scalar similarity scores,
  operational thresholds, latency metrics, and quality advisories.
- Employs Write-Ahead Logging (WAL) and thread-safe connection pooling.
"""

import os
import json
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from app.config import settings

_DB_LOCK = threading.Lock()
_START_TIME = datetime.now(timezone.utc)


def get_db_path() -> str:
    """Return verified absolute path to SQLite database."""
    path_str = settings.database_path
    db_file = Path(path_str).resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)
    return str(db_file)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a configured SQLite connection with row factory and WAL journal mode."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables and execute versioned schema migrations."""
    with _DB_LOCK:
        conn = get_connection(db_path)
        try:
            with conn:
                # Schema migrations tracking table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL
                    );
                """)

                # Check applied version
                cur = conn.cursor()
                cur.execute("SELECT MAX(version) FROM schema_migrations;")
                row = cur.fetchone()
                current_version = row[0] if (row and row[0] is not None) else 0

                # Migration 1: Initial audit log and benchmark history tables
                if current_version < 1:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS comparison_audit_log (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            probe_hash_prefix TEXT NOT NULL,
                            reference_hash_prefix TEXT NOT NULL,
                            similarity_score REAL,
                            display_score REAL,
                            threshold_used REAL NOT NULL,
                            threshold_profile TEXT NOT NULL,
                            is_match INTEGER NOT NULL,
                            latency_ms REAL NOT NULL,
                            face_count_a INTEGER NOT NULL,
                            face_count_b INTEGER NOT NULL,
                            quality_flags_a TEXT,
                            quality_flags_b TEXT,
                            status TEXT NOT NULL
                        );
                    """)

                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_comp_timestamp
                        ON comparison_audit_log(timestamp DESC);
                    """)

                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_comp_status
                        ON comparison_audit_log(status);
                    """)

                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS benchmark_runs (
                            run_id TEXT PRIMARY KEY,
                            dataset_id TEXT NOT NULL,
                            dataset_name TEXT NOT NULL,
                            timestamp TEXT NOT NULL,
                            total_pairs INTEGER NOT NULL,
                            accuracy REAL NOT NULL,
                            balanced_accuracy REAL NOT NULL,
                            eer REAL NOT NULL,
                            auc REAL NOT NULL,
                            optimal_threshold REAL NOT NULL,
                            duration_seconds REAL NOT NULL,
                            is_real INTEGER NOT NULL
                        );
                    """)

                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_bench_timestamp
                        ON benchmark_runs(timestamp DESC);
                    """)

                    conn.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?);",
                        (1, datetime.now(timezone.utc).isoformat()),
                    )
        finally:
            conn.close()


def record_comparison(
    probe_hash_prefix: str,
    reference_hash_prefix: str,
    similarity_score: Optional[float],
    display_score: Optional[float],
    threshold_used: float,
    threshold_profile: str,
    is_match: bool,
    latency_ms: float,
    face_count_a: int,
    face_count_b: int,
    quality_flags_a: List[str],
    quality_flags_b: List[str],
    status: str = "SUCCESS",
    db_path: Optional[str] = None,
) -> int:
    """Record anonymized pairwise comparison audit metadata to SQLite."""
    if not settings.audit_logging_enabled:
        return 0

    now_iso = datetime.now(timezone.utc).isoformat()
    flags_a_json = json.dumps(quality_flags_a)
    flags_b_json = json.dumps(quality_flags_b)
    is_match_int = 1 if is_match else 0

    with _DB_LOCK:
        conn = get_connection(db_path)
        try:
            with conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO comparison_audit_log (
                        timestamp, probe_hash_prefix, reference_hash_prefix,
                        similarity_score, display_score, threshold_used,
                        threshold_profile, is_match, latency_ms,
                        face_count_a, face_count_b, quality_flags_a,
                        quality_flags_b, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        now_iso,
                        probe_hash_prefix,
                        reference_hash_prefix,
                        similarity_score,
                        display_score,
                        threshold_used,
                        threshold_profile,
                        is_match_int,
                        latency_ms,
                        face_count_a,
                        face_count_b,
                        flags_a_json,
                        flags_b_json,
                        status,
                    ),
                )
                return cur.lastrowid or 0
        finally:
            conn.close()


def get_recent_comparisons(limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve recent comparison audit records ordered chronologically descending."""
    with _DB_LOCK:
        conn = get_connection(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, timestamp, probe_hash_prefix, reference_hash_prefix,
                       similarity_score, display_score, threshold_used,
                       threshold_profile, is_match, latency_ms,
                       face_count_a, face_count_b, quality_flags_a,
                       quality_flags_b, status
                FROM comparison_audit_log
                ORDER BY timestamp DESC
                LIMIT ?;
                """,
                (limit,),
            )
            rows = cur.fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": str(r["id"]),
                    "timestamp": r["timestamp"],
                    "probe_hash_prefix": r["probe_hash_prefix"],
                    "reference_hash_prefix": r["reference_hash_prefix"],
                    "similarity_score": r["similarity_score"],
                    "display_score": r["display_score"],
                    "threshold_used": r["threshold_used"],
                    "threshold_profile": r["threshold_profile"],
                    "decision": "MATCH" if r["is_match"] else "NO_MATCH",
                    "is_match": bool(r["is_match"]),
                    "inference_latency_ms": round(float(r["latency_ms"]), 2),
                    "latency_ms": round(float(r["latency_ms"]), 2),
                    "face_count_a": r["face_count_a"],
                    "face_count_b": r["face_count_b"],
                    "quality_flags_a": json.loads(r["quality_flags_a"]) if r["quality_flags_a"] else [],
                    "quality_flags_b": json.loads(r["quality_flags_b"]) if r["quality_flags_b"] else [],
                    "has_quality_warnings": bool(json.loads(r["quality_flags_a"]) or json.loads(r["quality_flags_b"])),
                    "status": r["status"],
                })
            return results
        finally:
            conn.close()


def clear_comparison_history(db_path: Optional[str] = None) -> int:
    """Clear all comparison audit records. Returns count of deleted records."""
    with _DB_LOCK:
        conn = get_connection(db_path)
        try:
            with conn:
                cur = conn.execute("DELETE FROM comparison_audit_log;")
                return cur.rowcount
        finally:
            conn.close()


def prune_comparison_audit_log(
    retention_days: Optional[int] = None,
    db_path: Optional[str] = None,
) -> int:
    """Delete comparison audit records older than the specified retention window (in days).

    Returns count of pruned records.
    """
    days = retention_days if retention_days is not None else settings.audit_retention_days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with _DB_LOCK:
        conn = get_connection(db_path)
        try:
            with conn:
                cur = conn.execute(
                    "DELETE FROM comparison_audit_log WHERE timestamp < ?;",
                    (cutoff,),
                )
                return cur.rowcount
        finally:
            conn.close()



def record_benchmark_run(
    run_id: str,
    dataset_id: str,
    dataset_name: str,
    total_pairs: int,
    accuracy: float,
    balanced_accuracy: float,
    eer: float,
    auc: float,
    optimal_threshold: float,
    duration_seconds: float,
    is_real: bool,
) -> None:
    """Record benchmark evaluation execution result to SQLite."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with _DB_LOCK:
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO benchmark_runs (
                        run_id, dataset_id, dataset_name, timestamp,
                        total_pairs, accuracy, balanced_accuracy, eer,
                        auc, optimal_threshold, duration_seconds, is_real
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        run_id,
                        dataset_id,
                        dataset_name,
                        now_iso,
                        total_pairs,
                        accuracy,
                        balanced_accuracy,
                        eer,
                        auc,
                        optimal_threshold,
                        duration_seconds,
                        1 if is_real else 0,
                    ),
                )
        finally:
            conn.close()


def get_all_benchmark_runs() -> List[Dict[str, Any]]:
    """Retrieve all recorded benchmark runs."""
    with _DB_LOCK:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT run_id, dataset_id, dataset_name, timestamp,
                       total_pairs, accuracy, balanced_accuracy, eer,
                       auc, optimal_threshold, duration_seconds, is_real
                FROM benchmark_runs
                ORDER BY timestamp DESC;
            """)
            rows = cur.fetchall()
            return [
                {
                    "run_id": r["run_id"],
                    "dataset_id": r["dataset_id"],
                    "dataset_name": r["dataset_name"],
                    "timestamp": r["timestamp"],
                    "total_pairs": r["total_pairs"],
                    "accuracy": r["accuracy"],
                    "balanced_accuracy": r["balanced_accuracy"],
                    "eer": r["eer"],
                    "auc": r["auc"],
                    "optimal_threshold": r["optimal_threshold"],
                    "duration_seconds": r["duration_seconds"],
                    "is_real": bool(r["is_real"]),
                }
                for r in rows
            ]
        finally:
            conn.close()


def get_dashboard_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calculate aggregated operational statistics for the production dashboard."""
    target_path = db_path or get_db_path()
    with _DB_LOCK:
        conn = get_connection(db_path)
        try:
            cur = conn.cursor()

            # Total comparisons
            cur.execute("SELECT COUNT(*) FROM comparison_audit_log;")
            total_comparisons = cur.fetchone()[0]

            # Completed successful comparisons
            cur.execute("SELECT COUNT(*) FROM comparison_audit_log WHERE status = 'SUCCESS';")
            successful_comparisons = cur.fetchone()[0]

            # Matches vs Non-matches
            cur.execute("SELECT COUNT(*) FROM comparison_audit_log WHERE status = 'SUCCESS' AND is_match = 1;")
            matches_count = cur.fetchone()[0]

            non_matches_count = max(0, successful_comparisons - matches_count)

            # Average latency
            cur.execute("SELECT AVG(latency_ms) FROM comparison_audit_log WHERE status = 'SUCCESS';")
            avg_lat_row = cur.fetchone()
            avg_latency = float(avg_lat_row[0]) if (avg_lat_row and avg_lat_row[0] is not None) else 0.0

            # Failures to Acquire (FTA)
            cur.execute("SELECT COUNT(*) FROM comparison_audit_log WHERE status LIKE 'FTA_%' OR status = 'FAILED' OR status = 'ERROR';")
            acquisition_failures = cur.fetchone()[0]

            fta_rate = float(acquisition_failures / total_comparisons) if total_comparisons > 0 else 0.0

            # FTA breakdown
            cur.execute("SELECT COUNT(*) FROM comparison_audit_log WHERE status = 'FTA_NO_FACE';")
            fta_no_face = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM comparison_audit_log WHERE status = 'FTA_MULTIPLE_FACES';")
            fta_multiple = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM comparison_audit_log WHERE status = 'ERROR' OR status = 'FAILED';")
            fta_error = cur.fetchone()[0]

            fta_breakdown = {
                "no_face_detected": fta_no_face,
                "multiple_faces_detected": fta_multiple,
                "processing_error": fta_error,
            }

            # Recent activity
            cur.execute(
                """
                SELECT id, timestamp, probe_hash_prefix, reference_hash_prefix,
                       similarity_score, display_score, threshold_used,
                       threshold_profile, is_match, latency_ms,
                       face_count_a, face_count_b, quality_flags_a,
                       quality_flags_b, status
                FROM comparison_audit_log
                ORDER BY timestamp DESC
                LIMIT 10;
                """
            )
            recent_rows = cur.fetchall()
            recent_activity = [
                {
                    "id": str(r["id"]),
                    "timestamp": r["timestamp"],
                    "probe_hash_prefix": r["probe_hash_prefix"],
                    "reference_hash_prefix": r["reference_hash_prefix"],
                    "similarity_score": r["similarity_score"],
                    "display_score": r["display_score"],
                    "threshold_used": r["threshold_used"],
                    "threshold_profile": r["threshold_profile"],
                    "decision": "MATCH" if r["is_match"] else "NO_MATCH",
                    "is_match": bool(r["is_match"]),
                    "latency_ms": round(float(r["latency_ms"]), 2),
                    "inference_latency_ms": round(float(r["latency_ms"]), 2),
                    "face_count_a": r["face_count_a"],
                    "face_count_b": r["face_count_b"],
                    "quality_flags_a": json.loads(r["quality_flags_a"]) if r["quality_flags_a"] else [],
                    "quality_flags_b": json.loads(r["quality_flags_b"]) if r["quality_flags_b"] else [],
                    "has_quality_warnings": bool(json.loads(r["quality_flags_a"]) or json.loads(r["quality_flags_b"])),
                    "status": r["status"],
                }
                for r in recent_rows
            ]

            # Benchmark summary
            cur.execute("""
                SELECT dataset_id, dataset_name, total_pairs, accuracy, balanced_accuracy, eer, auc, timestamp
                FROM benchmark_runs
                ORDER BY timestamp DESC
                LIMIT 5;
            """)
            bench_rows = cur.fetchall()
            benchmarks_summary = [
                {
                    "dataset_id": b["dataset_id"],
                    "dataset_name": b["dataset_name"],
                    "total_pairs": b["total_pairs"],
                    "accuracy": b["accuracy"],
                    "balanced_accuracy": b["balanced_accuracy"],
                    "eer": b["eer"],
                    "auc": b["auc"],
                    "timestamp": b["timestamp"],
                }
                for b in bench_rows
            ]

            uptime = (datetime.now(timezone.utc) - _START_TIME).total_seconds()
            db_size = os.path.getsize(target_path) if os.path.exists(target_path) else 0

            return {
                "total_comparisons": total_comparisons,
                "successful_comparisons": successful_comparisons,
                "successful_matches": matches_count,
                "successful_non_matches": non_matches_count,
                "matches_count": matches_count,
                "non_matches_count": non_matches_count,
                "failed_comparisons": acquisition_failures,
                "total_fta_events": acquisition_failures,
                "average_latency_ms": round(avg_latency, 2),
                "acquisition_failures": acquisition_failures,
                "fta_rate": round(fta_rate, 4),
                "fta_rate_percent": round(fta_rate * 100.0, 2),
                "fta_breakdown": fta_breakdown,
                "recent_activity": recent_activity,
                "benchmarks_summary": benchmarks_summary,
                "uptime_seconds": round(uptime, 1),
                "database_size_bytes": db_size,
                "schema_version": 1,
            }
        finally:
            conn.close()
