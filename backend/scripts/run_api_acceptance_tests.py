#!/usr/bin/env python3
"""FACECORE AI — Live API Integration Acceptance Test Suite (Step 11).

Executes comprehensive live HTTP integration tests against the actual running backend
without any mocks or synthetic shortcuts.
"""

import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8001"
LFW_ROOT = Path("backend/data/lfw/images")

def create_image_bytes(width: int, height: int, fmt: str = "JPEG", color: tuple = (128, 128, 128)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format=fmt)
    return buf.getvalue()

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
    content_type = f"multipart/form-data; boundary={boundary}"
    return bytes(body), content_type

def http_get(endpoint: str) -> tuple[int, dict]:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return resp.status, data
    except urllib.error.HTTPError as exc:
        data = json.loads(exc.read().decode("utf-8")) if exc.fp else {}
        return exc.code, data

def http_delete(endpoint: str) -> tuple[int, dict]:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return resp.status, data
    except urllib.error.HTTPError as exc:
        data = json.loads(exc.read().decode("utf-8")) if exc.fp else {}
        return exc.code, data

def http_post_multipart(endpoint: str, fields: dict, files: dict) -> tuple[int, dict]:
    url = f"{BASE_URL}{endpoint}"
    body, content_type = multipart_encode(fields, files)
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return resp.status, data
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            data = json.loads(raw)
        except Exception:
            data = {"raw": raw}
        return exc.code, data


def run_acceptance_tests() -> dict:
    results = {}
    
    print("=" * 70)
    print(" FACECORE AI — Live API Acceptance Suite Execution")
    print(f" Target Endpoint: {BASE_URL}")
    print("=" * 70)
    
    # 1. System Endpoints
    print("\n[GROUP 1] Testing System Health & Readiness Endpoints...")
    status, health = http_get("/api/health")
    assert status == 200, f"Health returned {status}"
    assert health["status"] == "ok"
    assert "1.0.0" in health["version"]
    print(f"  ✓ GET /api/health -> 200 OK (Version: {health['version']}, Status: {health['engine_status']})")
    results["health"] = health
    
    status, ready = http_get("/api/ready")
    assert status == 200, f"Ready returned {status}"
    assert ready["engine_ready"] is True
    print(f"  ✓ GET /api/ready -> 200 OK (Engine Ready: {ready['engine_ready']}, DB Ready: {ready['database_ready']})")
    results["ready"] = ready
    
    status, info = http_get("/api/engine-info")
    assert status == 200, f"Engine info returned {status}"
    assert "SFace" in info["name"]
    assert info["embedding_dimension"] == 128
    assert info["is_mock_data"] is False
    print(f"  ✓ GET /api/engine-info -> 200 OK (Engine: {info['name']}, Embedding Dim: {info['embedding_dimension']}, Mock: {info['is_mock_data']})")
    results["engine_info"] = info
    
    # 2. Image Validation Endpoints
    print("\n[GROUP 2] Testing Image Validation & Safeguard Gates...")
    # 2a: Valid JPEG
    jpeg_bytes = create_image_bytes(250, 250, "JPEG")
    status, val_jpeg = http_post_multipart("/api/validate-image", {}, {"file": ("test.jpg", jpeg_bytes, "image/jpeg")})
    assert status == 200 and val_jpeg["is_valid"] is True
    print(f"  ✓ Valid JPEG (250x250) -> Valid: {val_jpeg['is_valid']}, Format: {val_jpeg['diagnostics']['format']}")
    
    # 2b: Valid PNG
    png_bytes = create_image_bytes(300, 300, "PNG")
    status, val_png = http_post_multipart("/api/validate-image", {}, {"file": ("test.png", png_bytes, "image/png")})
    assert status == 200 and val_png["is_valid"] is True
    print(f"  ✓ Valid PNG (300x300) -> Valid: {val_png['is_valid']}, Format: {val_png['diagnostics']['format']}")

    # 2c: Valid WebP
    webp_bytes = create_image_bytes(200, 200, "WEBP")
    status, val_webp = http_post_multipart("/api/validate-image", {}, {"file": ("test.webp", webp_bytes, "image/webp")})
    assert status == 200 and val_webp["is_valid"] is True
    print(f"  ✓ Valid WebP (200x200) -> Valid: {val_webp['is_valid']}, Format: {val_webp['diagnostics']['format']}")
    
    # 2d: Corrupt image bytes
    corrupt_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00CorruptStreamTruncated"
    status, val_corrupt = http_post_multipart("/api/validate-image", {}, {"file": ("bad.jpg", corrupt_bytes, "image/jpeg")})
    assert status == 200 and val_corrupt["is_valid"] is False
    print(f"  ✓ Corrupt bytes rejected -> Valid: False, Reason: '{val_corrupt['error_message']}'")
    
    # 2e: Extension spoofing (text file pretending to be jpg)
    spoof_bytes = b"MZ\x90\x00FakePEHeaderExecutingPlainText"
    status, val_spoof = http_post_multipart("/api/validate-image", {}, {"file": ("malicious.jpg", spoof_bytes, "image/jpeg")})
    assert status == 200 and val_spoof["is_valid"] is False
    assert "Invalid or unsupported file signature" in val_spoof["error_message"]
    print(f"  ✓ Extension spoof rejected -> Valid: False, Reason: '{val_spoof['error_message']}'")
    
    # 2f: Sub-minimum dimension (< 48x48)
    tiny_bytes = create_image_bytes(32, 32, "PNG")
    status, val_tiny = http_post_multipart("/api/validate-image", {}, {"file": ("tiny.png", tiny_bytes, "image/png")})
    assert status == 200 and val_tiny["is_valid"] is False
    assert "resolution too low" in val_tiny["error_message"].lower()
    print(f"  ✓ Sub-48px rejected -> Valid: False, Reason: '{val_tiny['error_message']}'")

    # 2g: Oversized file payload (> 15MB)
    huge_bytes = b"\xFF\xD8\xFF" + b"\x00" * (16 * 1024 * 1024)
    status, val_huge = http_post_multipart("/api/validate-image", {}, {"file": ("huge.jpg", huge_bytes, "image/jpeg")})
    assert status == 200 and val_huge["is_valid"] is False
    assert "exceeds maximum allowed limit" in val_huge["error_message"].lower()
    print(f"  ✓ Oversized payload (>15MB) rejected -> Valid: False, Reason: '{val_huge['error_message']}'")

    # 3. Real Face Comparison Endpoints
    print("\n[GROUP 3] Testing Real Face Comparison & Profiles...")
    # Locate sample real photographs from LFW
    img_bush_1 = LFW_ROOT / "George_W_Bush" / "George_W_Bush_0001.jpg"
    img_bush_2 = LFW_ROOT / "George_W_Bush" / "George_W_Bush_0002.jpg"
    img_powell = LFW_ROOT / "Colin_Powell" / "Colin_Powell_0001.jpg"
    
    assert img_bush_1.is_file(), f"Missing {img_bush_1}"
    assert img_bush_2.is_file(), f"Missing {img_bush_2}"
    assert img_powell.is_file(), f"Missing {img_powell}"
    
    bush1_bytes = img_bush_1.read_bytes()
    bush2_bytes = img_bush_2.read_bytes()
    powell_bytes = img_powell.read_bytes()
    
    # 3a: Identical image comparison
    status, comp_ident = http_post_multipart(
        "/api/compare",
        {"threshold_profile": "balanced"},
        {"image_a": ("bush1.jpg", bush1_bytes, "image/jpeg"), "image_b": ("bush1.jpg", bush1_bytes, "image/jpeg")},
    )
    assert status == 200
    assert comp_ident["similarity_score"] > 0.98
    assert comp_ident["decision"] == "MATCH"
    lat_ident = comp_ident.get("inference_latency_ms", 0.0)
    print(f"  ✓ Identical pair -> Score: {comp_ident['similarity_score']:.4f}, Decision: {comp_ident['decision']}, Latency: {lat_ident:.1f}ms")

    # 3b: Genuine pair (same person, two different real photos)
    status, comp_gen = http_post_multipart(
        "/api/compare",
        {"threshold_profile": "balanced"},
        {"image_a": ("bush1.jpg", bush1_bytes, "image/jpeg"), "image_b": ("bush2.jpg", bush2_bytes, "image/jpeg")},
    )
    assert status == 200
    assert comp_gen["similarity_score"] > 0.40
    assert comp_gen["decision"] == "MATCH"
    lat_gen = comp_gen.get("inference_latency_ms", 0.0)
    print(f"  ✓ Genuine pair (Bush 1 vs 2) -> Score: {comp_gen['similarity_score']:.4f}, Decision: {comp_gen['decision']}, Latency: {lat_gen:.1f}ms")

    # 3c: Impostor pair (different persons: Bush vs Powell)
    status, comp_imp = http_post_multipart(
        "/api/compare",
        {"threshold_profile": "balanced"},
        {"image_a": ("bush1.jpg", bush1_bytes, "image/jpeg"), "image_b": ("powell.jpg", powell_bytes, "image/jpeg")},
    )
    assert status == 200
    assert comp_imp["similarity_score"] < 0.3132
    assert comp_imp["decision"] == "NO_MATCH"
    lat_imp = comp_imp.get("inference_latency_ms", 0.0)
    print(f"  ✓ Impostor pair (Bush vs Powell) -> Score: {comp_imp['similarity_score']:.4f}, Decision: {comp_imp['decision']}, Latency: {lat_imp:.1f}ms")

    # 3d: No face detected rejection
    blank_bytes = create_image_bytes(200, 200, "JPEG", color=(100, 100, 100))
    status, comp_noface = http_post_multipart(
        "/api/compare",
        {},
        {"image_a": ("blank.jpg", blank_bytes, "image/jpeg"), "image_b": ("bush1.jpg", bush1_bytes, "image/jpeg")},
    )
    assert status == 422
    assert "No face detected" in comp_noface.get("detail", "")
    print(f"  ✓ No face detected rejected -> Status: {status}, Detail: '{comp_noface.get('detail')}'")

    # 3e: Threshold profile evaluation
    profiles = ["high_security", "balanced", "high_convenience"]
    for prof in profiles:
        status, comp_prof = http_post_multipart(
            "/api/compare",
            {"threshold_profile": prof},
            {"image_a": ("bush1.jpg", bush1_bytes, "image/jpeg"), "image_b": ("bush2.jpg", bush2_bytes, "image/jpeg")},
        )
        assert status == 200
        print(f"  ✓ Profile '{prof}' -> Threshold: {comp_prof['threshold_used']:.4f}, Decision: {comp_prof['decision']}")

    # 3f: Custom threshold evaluation
    status, comp_cust = http_post_multipart(
        "/api/compare",
        {"threshold_profile": "custom", "custom_threshold": "0.7500"},
        {"image_a": ("bush1.jpg", bush1_bytes, "image/jpeg"), "image_b": ("bush2.jpg", bush2_bytes, "image/jpeg")},
    )
    assert status == 200
    assert comp_cust["threshold_used"] == 0.7500
    print(f"  ✓ Profile 'custom' (0.7500) -> Threshold: {comp_cust['threshold_used']:.4f}, Decision: {comp_cust['decision']}")

    # 3g: Manual bounding box crop coordinates
    status, comp_crop = http_post_multipart(
        "/api/compare",
        {"threshold_profile": "balanced", "crop_box_a": "[40, 30, 170, 190]"},
        {"image_a": ("bush1.jpg", bush1_bytes, "image/jpeg"), "image_b": ("bush2.jpg", bush2_bytes, "image/jpeg")},
    )
    assert status == 200
    print(f"  ✓ Bounding box crop -> Score: {comp_crop['similarity_score']:.4f}, Decision: {comp_crop['decision']}")

    # 3h: Explicit face selection index
    status, comp_sel = http_post_multipart(
        "/api/compare",
        {"threshold_profile": "balanced", "face_index_a": "0", "face_index_b": "0"},
        {"image_a": ("bush1.jpg", bush1_bytes, "image/jpeg"), "image_b": ("bush2.jpg", bush2_bytes, "image/jpeg")},
    )
    assert status == 200
    print(f"  ✓ Explicit face selection (index 0) -> Score: {comp_sel['similarity_score']:.4f}, Decision: {comp_sel['decision']}")

    # 4. Dashboard & Persistence Endpoints
    print("\n[GROUP 4] Testing Dashboard Statistics & Audit Trail...")
    status, stats = http_get("/api/dashboard/stats")
    assert status == 200
    assert stats["total_comparisons"] > 0
    print(f"  ✓ GET /api/dashboard/stats -> Total: {stats['total_comparisons']}, Matches: {stats['matches_count']}, FTA: {stats['acquisition_failures']}")

    status, hist = http_get("/api/history?limit=10")
    assert status == 200
    assert isinstance(hist, list)
    print(f"  ✓ GET /api/history -> Returned {len(hist)} records. Top item: id={hist[0]['id']}, score={hist[0]['similarity_score']}")

    # 5. Benchmarks Endpoints
    print("\n[GROUP 5] Testing Benchmarks Endpoints...")
    status, datasets = http_get("/api/benchmarks/datasets")
    assert status == 200
    assert isinstance(datasets, list)
    dataset_ids = [d["dataset_id"] for d in datasets]
    print(f"  ✓ GET /api/benchmarks/datasets -> Datasets available: {dataset_ids}")

    status, runs = http_get("/api/benchmarks/history")
    assert status == 200
    assert isinstance(runs, list)
    print(f"  ✓ GET /api/benchmarks/history -> Returned {len(runs)} benchmark runs")

    # 6. History Management & Pruning
    print("\n[GROUP 6] Testing History Deletion & Pruning...")
    status, del_resp = http_delete("/api/history?older_than_days=90")
    assert status == 200
    print(f"  ✓ DELETE /api/history?older_than_days=90 -> Pruned: {del_resp.get('deleted_count', 0)}")

    print("\n" + "=" * 70)
    print(" ALL API INTEGRATION ACCEPTANCE CHECKS PASSED (100% LIVE VERIFICATION)")
    print("=" * 70)
    return results

if __name__ == "__main__":
    run_acceptance_tests()
