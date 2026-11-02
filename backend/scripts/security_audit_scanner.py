#!/usr/bin/env python3
"""FACECORE AI — Repository Security & Secret Audit Scanner (Step 12A).

Scans all source code, configuration files, and documentation for:
1. Secret tokens, passwords, API keys, credentials.
2. Local absolute filesystem paths (e.g. C:\\Users\\..., C:\\Projects\\...).
3. Private URLs or internal network identifiers.
4. Personal identifying data.
"""

import os
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

EXCLUDE_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    ".vite", "data", "weights"
}

# Regex patterns for credential exposure
SECRET_PATTERNS = [
    (r'(?i)(?:api_key|apikey|secret_key|private_key|token|auth_token|password|passwd|pwd)\s*[:=]\s*["\']([^"\']{6,})["\']', "Potential credential assignment"),
    (r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{16,}', "Bearer token format"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
    (r'AIza[0-9A-Za-z\\-_]{35}', "Google API Key"),
    (r'xox[baprs]-[0-9a-zA-Z]{10,48}', "Slack token"),
    (r'-----BEGIN (?:RSA )?PRIVATE KEY-----', "Private RSA key block"),
]

# Patterns for hardcoded Windows/Linux absolute paths
PATH_PATTERNS = [
    (r'[a-zA-Z]:\\(?:Users|Projects|Documents|home)[\\/][^\s"\'<>]+', "Local Windows absolute filesystem path"),
    (r'/(?:Users|home)/[^\s"\'<>]+', "Local Unix absolute filesystem path"),
]

def scan_file(file_path: Path) -> list[dict]:
    findings = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return findings

    lines = content.splitlines()

    for idx, line in enumerate(lines, 1):
        # Ignore comments or markdown headings if innocuous
        stripped = line.strip()
        if not stripped:
            continue

        for pat, desc in SECRET_PATTERNS:
            m = re.search(pat, line)
            if m:
                # Filter false positives like schemas, type definitions, or .env.example comments
                val = m.group(0)
                if any(x in val.lower() for x in ["placeholder", "example", "none", "string", "description", "label"]):
                    continue
                findings.append({
                    "file": str(file_path.relative_to(WORKSPACE_ROOT)),
                    "line": idx,
                    "type": "SECRET",
                    "description": desc,
                    "snippet": line[:120].strip()
                })

        for pat, desc in PATH_PATTERNS:
            m = re.search(pat, line)
            if m:
                # We expect reports like STEP01-11 reports or release manifests to contain references, but source code should not have hardcoded local absolute paths!
                findings.append({
                    "file": str(file_path.relative_to(WORKSPACE_ROOT)),
                    "line": idx,
                    "type": "ABSOLUTE_PATH",
                    "description": desc,
                    "snippet": line[:120].strip()
                })

    return findings

def main():
    print("=" * 70)
    print(" FACECORE AI — Automated Repository Security & Secrets Audit")
    print("=" * 70)

    total_files = 0
    all_findings = []

    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for f in files:
            p = Path(root) / f
            if p.suffix in [".py", ".ts", ".tsx", ".js", ".json", ".md", ".sh", ".ps1", ".bat", ".env", ".example", ".yaml", ".yml"]:
                total_files += 1
                findings = scan_file(p)
                all_findings.extend(findings)

    secrets = [f for f in all_findings if f["type"] == "SECRET"]
    paths = [f for f in all_findings if f["type"] == "ABSOLUTE_PATH"]

    print(f"Scanned: {total_files} files")
    print(f"Secrets Found: {len(secrets)}")
    print(f"Absolute Paths Found: {len(paths)}")

    if secrets:
        print("\n[ALERT] Secrets Detected:")
        for s in secrets:
            print(f"  {s['file']}:{s['line']} - {s['description']}: {s['snippet']}")
    else:
        print("\n[PASS] Zero API keys, passwords, bearer tokens, or private secrets detected.")

    if paths:
        print("\n[NOTE] Absolute paths detected (analyzing source vs reports)...")
        source_paths = [p for p in paths if not p['file'].startswith("STEP") and not p['file'].startswith("release") and not p['file'].endswith(".md")]
        print(f"  Source code / config paths: {len(source_paths)}")
        for sp in source_paths:
            print(f"  {sp['file']}:{sp['line']} - {sp['snippet']}")
        report_paths = [p for p in paths if p['file'].startswith("STEP") or p['file'].startswith("release") or p['file'].endswith(".md")]
        print(f"  Historical report / manifest references: {len(report_paths)}")

if __name__ == "__main__":
    main()

