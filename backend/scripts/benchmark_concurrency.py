#!/usr/bin/env python3
"""FACECORE AI — Concurrency, Throughput & Memory Stress Benchmark (Step 11).

Dispatches 1, 2, 5, and 10 concurrent requests to /api/compare with authentic LFW images,
measuring latency percentiles, throughput (req/s), inference lock serialization, and
memory stability.
"""

from __future__ import annotations

import concurrent.futures
import ctypes
from ctypes import wintypes
import json
import os
import re
import statistics
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8001"
LFW_ROOT = Path("backend/data/lfw/images")


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def get_pid_on_port(port: int = 8001) -> int | None:
    """Find PID of process listening on specified TCP port."""
    try:
        out = subprocess.check_output(f"netstat -ano", shell=True, text=True)
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                return int(parts[-1])
    except Exception:
        pass
    return None


def get_process_memory_mb(pid: int) -> float:
    """Query working set memory in MB via Windows Win32 API."""
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    handle = ctypes.windll.kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid
    )
    if not handle:
        return 0.0
    try:
        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        if ctypes.windll.psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        ):
            return counters.WorkingSetSize / (1024 * 1024)
        return 0.0
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def multipart_encode(fields: dict, files: dict) -> tuple[bytes, str]:
    boundary = "----WebKitFormBoundary" + hex(int(time.time() * 1000))[2:]
    body = bytearray()
    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        body.extend(f"{v}\r\n".encode())
    for k, (filename, data, content_type) in files.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"\r\n'.encode())
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(data)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def send_comparison_request(payload_bytes: bytes, content_type: str) -> tuple[bool, float, dict]:
    """Execute single HTTP request and record wall-clock round trip latency."""
    url = f"{BASE_URL}/api/compare"
    req = urllib.request.Request(url, data=payload_bytes, method="POST")
    req.add_header("Content-Type", content_type)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return (resp.status == 200), elapsed_ms, data
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return False, elapsed_ms, {"error": str(exc)}


def run_concurrency_tier(
    concurrency: int,
    total_requests: int,
    payload_bytes: bytes,
    content_type: str,
    pid: int | None,
) -> dict:
    """Run a batch of requests at a fixed concurrency level."""
    latencies = []
    completed = 0
    failed = 0
    mem_readings = []

    if pid:
        mem_readings.append(get_process_memory_mb(pid))

    t_start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(send_comparison_request, payload_bytes, content_type)
            for _ in range(total_requests)
        ]
        for f in concurrent.futures.as_completed(futures):
            ok, lat, _ = f.result()
            latencies.append(lat)
            if ok:
                completed += 1
            else:
                failed += 1
            if pid and len(latencies) % max(1, total_requests // 4) == 0:
                mem_readings.append(get_process_memory_mb(pid))

    total_wall_sec = time.perf_counter() - t_start
    throughput = completed / total_wall_sec if total_wall_sec > 0 else 0.0

    sorted_lat = sorted(latencies)
    avg_lat = statistics.mean(latencies) if latencies else 0.0
    median_lat = statistics.median(latencies) if latencies else 0.0
    p95_lat = (
        sorted_lat[int(len(sorted_lat) * 0.95)]
        if sorted_lat
        else 0.0
    )
    min_lat = sorted_lat[0] if sorted_lat else 0.0
    max_lat = sorted_lat[-1] if sorted_lat else 0.0

    end_mem = get_process_memory_mb(pid) if pid else 0.0

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "completed": completed,
        "failed": failed,
        "wall_time_seconds": round(total_wall_sec, 2),
        "throughput_req_per_sec": round(throughput, 2),
        "avg_latency_ms": round(avg_lat, 2),
        "median_latency_ms": round(median_lat, 2),
        "p95_latency_ms": round(p95_lat, 2),
        "min_latency_ms": round(min_lat, 2),
        "max_latency_ms": round(max_lat, 2),
        "memory_readings_mb": [round(m, 1) for m in mem_readings] + [round(end_mem, 1)],
    }


def main():
    print("=" * 70)
    print(" FACECORE AI — Concurrency, Throughput & Memory Stress Benchmark")
    print("=" * 70)

    pid = get_pid_on_port(8001)
    print(f"Backend Server Process PID: {pid}")
    if pid:
        baseline_mem = get_process_memory_mb(pid)
        print(f"Initial Baseline Memory (Working Set): {baseline_mem:.2f} MB")
    else:
        baseline_mem = 0.0

    # Prepare real image payloads
    bush1_path = LFW_ROOT / "George_W_Bush" / "George_W_Bush_0001.jpg"
    bush2_path = LFW_ROOT / "George_W_Bush" / "George_W_Bush_0002.jpg"
    assert bush1_path.is_file() and bush2_path.is_file()

    payload_bytes, content_type = multipart_encode(
        {"threshold_profile": "balanced"},
        {
            "image_a": ("bush1.jpg", bush1_path.read_bytes(), "image/jpeg"),
            "image_b": ("bush2.jpg", bush2_path.read_bytes(), "image/jpeg"),
        },
    )

    tiers = [
        (1, 10),   # 1 concurrent, 10 requests (baseline serialization)
        (2, 10),   # 2 concurrent, 10 requests
        (5, 15),   # 5 concurrent, 15 requests
        (10, 20),  # 10 concurrent, 20 requests (stress level)
    ]

    tier_results = []
    total_stress_requests = sum(t[1] for t in tiers)

    for concurrency, n_req in tiers:
        print(f"\n--- Testing Concurrency Level: {concurrency} workers ({n_req} requests) ---")
        res = run_concurrency_tier(concurrency, n_req, payload_bytes, content_type, pid)
        tier_results.append(res)
        print(
            f"  Completed: {res['completed']}/{res['total_requests']} (Failed: {res['failed']})\n"
            f"  Throughput: {res['throughput_req_per_sec']} req/s\n"
            f"  Latency: Avg={res['avg_latency_ms']}ms | Med={res['median_latency_ms']}ms | P95={res['p95_latency_ms']}ms\n"
            f"  Memory Trend: {res['memory_readings_mb']} MB"
        )
        time.sleep(1.0)  # Brief cooldown

    # Sustained memory leak probe: 30 additional requests
    print("\n--- Testing Sustained Memory Stability (Post-Stress 30 Requests) ---")
    post_res = run_concurrency_tier(5, 30, payload_bytes, content_type, pid)
    print(
        f"  Completed: {post_res['completed']}/{post_res['total_requests']}\n"
        f"  Throughput: {post_res['throughput_req_per_sec']} req/s\n"
        f"  Memory Trend: {post_res['memory_readings_mb']} MB"
    )

    final_mem = get_process_memory_mb(pid) if pid else 0.0
    mem_delta = final_mem - baseline_mem
    total_run_requests = total_stress_requests + 30

    print("\n" + "=" * 70)
    print(f" TOTAL REQUESTS EVALUATED: {total_run_requests}")
    print(f" BASELINE MEMORY:          {baseline_mem:.2f} MB")
    print(f" FINAL MEMORY:             {final_mem:.2f} MB")
    print(f" NET MEMORY GROWTH:        {mem_delta:+.2f} MB")
    print("=" * 70)

    # Save structured JSON benchmark summary
    summary_data = {
        "server_pid": pid,
        "baseline_memory_mb": round(baseline_mem, 2),
        "final_memory_mb": round(final_mem, 2),
        "memory_delta_mb": round(mem_delta, 2),
        "total_requests": total_run_requests,
        "tiers": tier_results,
        "sustained_tier": post_res,
    }
    out_file = Path("backend/data/step11_concurrency_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    print(f"Wrote benchmark results to: {out_file}")


if __name__ == "__main__":
    main()

