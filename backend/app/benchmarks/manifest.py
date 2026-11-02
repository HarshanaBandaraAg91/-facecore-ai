"""Dataset manifest handling, pairs parsing, identity leakage checks, and fixture generation.

Ensures strict scientific integrity:
- Validates identity-disjoint train/validation/test partitions
- Detects data leakage across evaluation folds
- Provides deterministic pair generation from seed
- Bundles authorized local evaluation fixtures for offline testing
"""

import os
import io
import json
import hashlib
from typing import List, Dict, Tuple, Set, Optional, Any
import numpy as np
import cv2

from app.benchmarks.schemas import (
    DatasetMetadata,
    DatasetStatus,
    PairAnnotation,
)

DATASETS_REGISTRY: Dict[str, DatasetMetadata] = {
    "lfw-canonical-v1": DatasetMetadata(
        dataset_id="lfw-canonical-v1",
        name="Labeled Faces in the Wild (LFW)",
        description="Standard 10-fold unconstrained facial verification protocol across 6,000 official pairs. Requires local dataset images at local_path.",
        total_images=13233,
        total_identities=5749,
        total_pairs=6000,
        verification_status=DatasetStatus.UNRUN,
        is_available=False,  # Unmounted by default; requires verified local archive
        license="Non-Commercial Academic Research (UMass Amherst)",
        source_url="http://vis-www.cs.umass.edu/lfw/",
        local_path=None,
        dataset_type="real",
        installation_status="NOT_INSTALLED",
    ),
    "calfw-v1": DatasetMetadata(
        dataset_id="calfw-v1",
        name="Cross-Age LFW (CALFW)",
        description="Cross-age face verification benchmark across 6,000 pairs with maximized chronological age gaps and attribute-balanced impostors.",
        total_images=12174,
        total_identities=4025,
        total_pairs=6000,
        verification_status=DatasetStatus.UNRUN,
        is_available=False,
        license="Non-Commercial Academic Research (Tsinghua / BUPT)",
        source_url="http://whdeng.cn/CALFW/index.html",
        local_path=None,
        dataset_type="real",
        installation_status="NOT_INSTALLED",
    ),
    "cplfw-v1": DatasetMetadata(
        dataset_id="cplfw-v1",
        name="Cross-Pose LFW (CPLFW)",
        description="Cross-pose face verification benchmark across 6,000 pairs with maximized yaw variation and attribute-balanced impostors.",
        total_images=11652,
        total_identities=3998,
        total_pairs=6000,
        verification_status=DatasetStatus.UNRUN,
        is_available=False,
        license="Non-Commercial Academic Research (Tsinghua / BUPT)",
        source_url="http://whdeng.cn/CPLFW/index.html",
        local_path=None,
        dataset_type="real",
        installation_status="NOT_INSTALLED",
    ),
    "cfp-fp-v1": DatasetMetadata(
        dataset_id="cfp-fp-v1",
        name="Celebrities in Frontal-Profile (CFP-FP)",
        description="Extreme cross-pose verification benchmark (0 deg frontal vs 90 deg profile yaw) across 7,000 pairs.",
        total_images=7000,
        total_identities=500,
        total_pairs=7000,
        verification_status=DatasetStatus.UNRUN,
        is_available=False,
        license="Academic Research Agreement (UMD)",
        source_url="http://www.cfpdb.org/",
        local_path=None,
        dataset_type="real",
        installation_status="NOT_INSTALLED",
    ),
    "agedb-30-v1": DatasetMetadata(
        dataset_id="agedb-30-v1",
        name="AgeDB-30 (Temporal 30-Year Gap)",
        description="Cross-age verification benchmark evaluating image pairs with a 30-year chronological aging gap.",
        total_images=16488,
        total_identities=568,
        total_pairs=6000,
        verification_status=DatasetStatus.UNRUN,
        is_available=False,
        license="CC BY-NC 4.0 (Imperial College London iBUG)",
        source_url="https://ibug.doc.ic.ac.uk/resources/agedb/",
        local_path=None,
        dataset_type="real",
        installation_status="RESTRICTED_ACCESS",
    ),
    "fhibe-v1": DatasetMetadata(
        dataset_id="fhibe-v1",
        name="Fair Human-Centric Image Benchmark (FHIBE)",
        description="Consented multi-demographic fairness benchmark evaluating skin-tone (MST) and demographic balance.",
        total_images=100000,
        total_identities=10000,
        total_pairs=20000,
        verification_status=DatasetStatus.UNRUN,
        is_available=False,
        license="Custom Sony AI / Mozilla Data Collective Agreement",
        source_url="https://ai.sony/research/FHIBE/",
        local_path=None,
    ),
    "dfw-v1": DatasetMetadata(
        dataset_id="dfw-v1",
        name="Disguised Faces in the Wild (DFW)",
        description="Adversarial disguise, makeup, and impersonation verification benchmark.",
        total_images=11157,
        total_identities=1000,
        total_pairs=10000,
        verification_status=DatasetStatus.UNRUN,
        is_available=False,
        license="IIIT-Delhi Academic Research License",
        source_url="http://iab-rubric.org/resources/dfw.html",
        local_path=None,
    ),
    "facecore-synthetic-fixture-v1": DatasetMetadata(
        dataset_id="facecore-synthetic-fixture-v1",
        name="FACECORE Synthetic Benchmark Fixture",
        description="Deterministic local 10-fold verification benchmark (60 genuine, 60 impostor pairs) for instant offline CI.",
        total_images=120,
        total_identities=20,
        total_pairs=120,
        verification_status=DatasetStatus.DATASET_VERIFIED,
        is_available=True,
        license="Apache-2.0 (Internal Test Fixture)",
        source_url="local://fixtures/synthetic-v1",
        local_path="app/benchmarks/fixtures/synthetic_manifest.json",
        dataset_type="synthetic",
        installation_status="VERIFIED",
    ),
}


def sync_dataset_registry_with_disk() -> None:
    """Inspect local storage and dynamically update dataset availability and mounting paths."""
    # Check LFW
    candidates = [
        os.path.join("backend", "data", "lfw"),
        os.path.join("data", "lfw"),
    ]
    lfw_meta = DATASETS_REGISTRY.get("lfw-canonical-v1")
    for cand in candidates:
        pairs_p = os.path.join(cand, "pairs.txt")
        images_p = os.path.join(cand, "images")
        if not os.path.isdir(images_p) and os.path.isdir(os.path.join(cand, "lfw")):
            images_p = os.path.join(cand, "lfw")
        if os.path.isfile(pairs_p) and os.path.isdir(images_p):
            try:
                subdirs = [d for d in os.listdir(images_p) if os.path.isdir(os.path.join(images_p, d))]
                if len(subdirs) >= 100:
                    if lfw_meta:
                        lfw_meta.is_available = True
                        lfw_meta.verification_status = DatasetStatus.DATASET_VERIFIED
                        lfw_meta.installation_status = "VERIFIED"
                        lfw_meta.local_path = os.path.abspath(images_p)
                    break
            except OSError:
                pass

    # Check CALFW (Cross-Age LFW)
    calfw_meta = DATASETS_REGISTRY.get("calfw-v1")
    for cand_csv in [
        os.path.join("backend", "data", "calfw", "pairs.csv"),
        os.path.join("data", "calfw", "pairs.csv"),
    ]:
        if os.path.isfile(cand_csv) and lfw_meta and lfw_meta.is_available:
            if calfw_meta:
                calfw_meta.is_available = True
                calfw_meta.verification_status = DatasetStatus.DATASET_VERIFIED
                calfw_meta.installation_status = "VERIFIED"
                calfw_meta.local_path = os.path.abspath(os.path.dirname(cand_csv))
            break

    # Check CPLFW (Cross-Pose LFW)
    cplfw_meta = DATASETS_REGISTRY.get("cplfw-v1")
    for cand_csv in [
        os.path.join("backend", "data", "cplfw", "pairs.csv"),
        os.path.join("data", "cplfw", "pairs.csv"),
    ]:
        if os.path.isfile(cand_csv) and lfw_meta and lfw_meta.is_available:
            if cplfw_meta:
                cplfw_meta.is_available = True
                cplfw_meta.verification_status = DatasetStatus.DATASET_VERIFIED
                cplfw_meta.installation_status = "VERIFIED"
                cplfw_meta.local_path = os.path.abspath(os.path.dirname(cand_csv))
            break

    # Check CFP-FP
    cfp_meta = DATASETS_REGISTRY.get("cfp-fp-v1")
    for cand_cfp in [
        os.path.join("backend", "data", "cfp"),
        os.path.join("data", "cfp"),
    ]:
        pairs_p = os.path.join(cand_cfp, "Pair_list_P.txt")
        images_p = os.path.join(cand_cfp, "Images")
        if not os.path.isdir(images_p) and os.path.isdir(os.path.join(cand_cfp, "images")):
            images_p = os.path.join(cand_cfp, "images")
        if os.path.isfile(pairs_p) and os.path.isdir(images_p):
            if cfp_meta:
                cfp_meta.is_available = True
                cfp_meta.verification_status = DatasetStatus.DATASET_VERIFIED
                cfp_meta.installation_status = "VERIFIED"
                cfp_meta.local_path = os.path.abspath(cand_cfp)
            break

    # Check AgeDB-30
    agedb_meta = DATASETS_REGISTRY.get("agedb-30-v1")
    for cand_agedb in [
        os.path.join("backend", "data", "agedb"),
        os.path.join("data", "agedb"),
    ]:
        pairs_p = os.path.join(cand_agedb, "agedb_30_pair.txt")
        images_p = os.path.join(cand_agedb, "images")
        if os.path.isfile(pairs_p) and os.path.isdir(images_p):
            if agedb_meta:
                agedb_meta.is_available = True
                agedb_meta.verification_status = DatasetStatus.DATASET_VERIFIED
                agedb_meta.installation_status = "VERIFIED"
                agedb_meta.local_path = os.path.abspath(cand_agedb)
            break


sync_dataset_registry_with_disk()


def check_data_leakage(
    train_pairs: List[PairAnnotation],
    test_pairs: List[PairAnnotation],
) -> Tuple[bool, List[str]]:
    """Verify that train/validation partition and test partition share zero subject identities.

    Returns:
    - has_leakage (bool): True if identity overlap is found
    - violations (List[str]): List of leaking identity names
    """
    train_identities: Set[str] = set()
    for p in train_pairs:
        train_identities.add(p.identity_a)
        train_identities.add(p.identity_b)

    test_identities: Set[str] = set()
    for p in test_pairs:
        test_identities.add(p.identity_a)
        test_identities.add(p.identity_b)

    leaking = sorted(list(train_identities.intersection(test_identities)))
    return (len(leaking) > 0, leaking)


def check_duplicate_pairs(pairs: List[PairAnnotation]) -> List[str]:
    """Detect duplicate image pairings (regardless of probe/reference order)."""
    seen: Set[str] = set()
    duplicates: List[str] = []

    for p in pairs:
        # Standardize pair hash
        endpoints = sorted([p.image_a, p.image_b])
        pair_key = f"{endpoints[0]}:::{endpoints[1]}"
        if pair_key in seen:
            duplicates.append(p.pair_id)
        seen.add(pair_key)

    return duplicates


def parse_lfw_pairs_txt(lines: List[str]) -> List[PairAnnotation]:
    """Parse standard LFW format pairs.txt lines into structured PairAnnotations.

    Standard LFW format:
    - Line 1: `10 300` (10 folds, 300 genuine + 300 impostor per fold)
    - Subsequent lines per fold:
        - 300 lines: `name  img_num1  img_num2` (Genuine)
        - 300 lines: `name1  img_num1  name2  img_num2` (Impostor)
    """
    if not lines or len(lines) < 2:
        raise ValueError("LFW pairs file is empty or malformed.")

    header = lines[0].strip().split()
    if len(header) != 2:
        raise ValueError(f"Invalid LFW header line: '{lines[0]}'. Expected 'num_folds pairs_per_fold'.")

    num_folds = int(header[0])
    pairs_per_fold = int(header[1])

    annotations: List[PairAnnotation] = []
    line_idx = 1
    total_lines = len(lines)

    for fold in range(num_folds):
        # Read genuine pairs
        for _ in range(pairs_per_fold):
            if line_idx >= total_lines:
                break
            parts = lines[line_idx].strip().split()
            line_idx += 1
            if len(parts) >= 3:
                name, num1, num2 = parts[0], parts[1], parts[2]
                annotations.append(
                    PairAnnotation(
                        pair_id=f"fold_{fold}_gen_{name}_{num1}_{num2}",
                        image_a=f"{name}/{name}_{int(num1):04d}.jpg",
                        image_b=f"{name}/{name}_{int(num2):04d}.jpg",
                        is_genuine=True,
                        identity_a=name,
                        identity_b=name,
                        fold_index=fold,
                        condition="baseline",
                    )
                )

        # Read impostor pairs
        for _ in range(pairs_per_fold):
            if line_idx >= total_lines:
                break
            parts = lines[line_idx].strip().split()
            line_idx += 1
            if len(parts) >= 4:
                name1, num1, name2, num2 = parts[0], parts[1], parts[2], parts[3]
                annotations.append(
                    PairAnnotation(
                        pair_id=f"fold_{fold}_imp_{name1}_{num1}_{name2}_{num2}",
                        image_a=f"{name1}/{name1}_{int(num1):04d}.jpg",
                        image_b=f"{name2}/{name2}_{int(num2):04d}.jpg",
                        is_genuine=False,
                        identity_a=name1,
                        identity_b=name2,
                        fold_index=fold,
                        condition="baseline",
                    )
                )

    return annotations


def parse_calfw_pairs_csv(
    csv_content: str,
    images_base: str,
    require_all: bool = False,
    return_unresolved: bool = False,
) -> Any:
    """Parse CALFW (Cross-Age LFW) pairs.csv into structured PairAnnotations.
    
    If return_unresolved=True, returns (pairs, unresolved_records, missing_images_set).
    """
    import csv
    reader = csv.DictReader(io.StringIO(csv_content))
    pairs: List[PairAnnotation] = []
    unresolved_records: List[Dict[str, Any]] = []
    missing_images: Set[str] = set()

    for row in reader:
        img_a = row["image_a"]
        img_b = row["image_b"]
        id_a = img_a.rsplit("_", 1)[0]
        id_b = img_b.rsplit("_", 1)[0]
        rel_a = f"{id_a}/{img_a}"
        rel_b = f"{id_b}/{img_b}"
        is_gen = bool(int(row["is_same"]))
        fold = int(row["fold_id"]) - 1

        path_a = os.path.join(images_base, rel_a)
        path_b = os.path.join(images_base, rel_b)
        has_a = os.path.isfile(path_a)
        has_b = os.path.isfile(path_b)

        if not (has_a and has_b):
            if not has_a:
                missing_images.add(rel_a)
            if not has_b:
                missing_images.add(rel_b)
            unresolved_records.append({
                "pair_id": f"calfw_{fold}_{row['fold_position']}_{'gen' if is_gen else 'imp'}",
                "fold": fold,
                "is_same": is_gen,
                "image_a": rel_a,
                "image_b": rel_b,
                "has_a": has_a,
                "has_b": has_b,
            })
            if require_all:
                raise ValueError(f"CALFW image missing on disk: '{rel_a}' or '{rel_b}'")
            continue

        pairs.append(
            PairAnnotation(
                pair_id=f"calfw_{fold}_{row['fold_position']}_{'gen' if is_gen else 'imp'}",
                image_a=rel_a,
                image_b=rel_b,
                is_genuine=is_gen,
                identity_a=id_a,
                identity_b=id_b,
                fold_index=fold,
                condition="cross_age",
            )
        )

    if return_unresolved:
        return pairs, unresolved_records, missing_images
    return pairs


def parse_cplfw_pairs_csv(
    csv_content: str,
    images_base: str,
    require_all: bool = False,
    return_unresolved: bool = False,
) -> Any:
    """Parse CPLFW (Cross-Pose LFW) pairs.csv into structured PairAnnotations.
    
    If return_unresolved=True, returns (pairs, unresolved_records, missing_images_set).
    """
    import csv
    reader = csv.DictReader(io.StringIO(csv_content))
    pairs: List[PairAnnotation] = []
    unresolved_records: List[Dict[str, Any]] = []
    missing_images: Set[str] = set()

    for row in reader:
        img_a = row["image_a"]
        img_b = row["image_b"]
        id_a, idx_a = img_a.rsplit("_", 1)
        id_b, idx_b = img_b.rsplit("_", 1)
        canon_a = f"{id_a}_{int(idx_a.split('.')[0]):04d}.jpg"
        canon_b = f"{id_b}_{int(idx_b.split('.')[0]):04d}.jpg"
        rel_a = f"{id_a}/{canon_a}"
        rel_b = f"{id_b}/{canon_b}"
        is_gen = bool(int(row["is_same"]))
        fold = int(row["fold_id"]) - 1

        path_a = os.path.join(images_base, rel_a)
        path_b = os.path.join(images_base, rel_b)
        has_a = os.path.isfile(path_a)
        has_b = os.path.isfile(path_b)

        if not (has_a and has_b):
            if not has_a:
                missing_images.add(rel_a)
            if not has_b:
                missing_images.add(rel_b)
            unresolved_records.append({
                "pair_id": f"cplfw_{fold}_{row['fold_position']}_{'gen' if is_gen else 'imp'}",
                "fold": fold,
                "is_same": is_gen,
                "image_a": rel_a,
                "image_b": rel_b,
                "has_a": has_a,
                "has_b": has_b,
            })
            if require_all:
                raise ValueError(f"CPLFW image missing on disk: '{rel_a}' or '{rel_b}'")
            continue

        pairs.append(
            PairAnnotation(
                pair_id=f"cplfw_{fold}_{row['fold_position']}_{'gen' if is_gen else 'imp'}",
                image_a=rel_a,
                image_b=rel_b,
                is_genuine=is_gen,
                identity_a=id_a,
                identity_b=id_b,
                fold_index=fold,
                condition="cross_pose",
            )
        )

    if return_unresolved:
        return pairs, unresolved_records, missing_images
    return pairs


def parse_cfp_fp_pairs_txt(
    lines: List[str],
    images_base: str,
    require_all: bool = False,
) -> List[PairAnnotation]:
    """Parse Celebrities in Frontal-Profile (CFP-FP) pair list format."""
    pairs: List[PairAnnotation] = []
    fold_idx = 0
    fold_counter = 0

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        rel_a, rel_b, lbl_str = parts[0], parts[1], parts[2]
        is_gen = (lbl_str == "1")

        id_a = os.path.dirname(rel_a) or rel_a.split("_")[0]
        id_b = os.path.dirname(rel_b) or rel_b.split("_")[0]

        path_a = os.path.join(images_base, rel_a)
        path_b = os.path.join(images_base, rel_b)
        if not (os.path.isfile(path_a) and os.path.isfile(path_b)):
            if require_all:
                raise ValueError(f"CFP-FP image missing: '{rel_a}' or '{rel_b}'")
            continue

        pairs.append(
            PairAnnotation(
                pair_id=f"cfp_fp_{fold_idx}_{fold_counter}_{'gen' if is_gen else 'imp'}",
                image_a=rel_a,
                image_b=rel_b,
                is_genuine=is_gen,
                identity_a=id_a,
                identity_b=id_b,
                fold_index=fold_idx,
                condition="frontal_profile",
            )
        )
        fold_counter += 1
        if fold_counter >= 700:
            fold_counter = 0
            fold_idx = min(9, fold_idx + 1)

    return pairs


def parse_agedb_pairs_txt(
    lines: List[str],
    images_base: str,
    require_all: bool = False,
) -> List[PairAnnotation]:
    """Parse AgeDB-30 pair list format."""
    pairs: List[PairAnnotation] = []
    fold_idx = 0
    fold_counter = 0

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        img_a, img_b, lbl_str = parts[0], parts[1], parts[2]
        is_gen = (lbl_str == "1")

        id_a = img_a.rsplit("_", 2)[0]
        id_b = img_b.rsplit("_", 2)[0]

        path_a = os.path.join(images_base, img_a)
        path_b = os.path.join(images_base, img_b)
        if not (os.path.isfile(path_a) and os.path.isfile(path_b)):
            if require_all:
                raise ValueError(f"AgeDB-30 image missing: '{img_a}' or '{img_b}'")
            continue

        pairs.append(
            PairAnnotation(
                pair_id=f"agedb30_{fold_idx}_{fold_counter}_{'gen' if is_gen else 'imp'}",
                image_a=img_a,
                image_b=img_b,
                is_genuine=is_gen,
                identity_a=id_a,
                identity_b=id_b,
                fold_index=fold_idx,
                condition="cross_age_30yr",
            )
        )
        fold_counter += 1
        if fold_counter >= 600:
            fold_counter = 0
            fold_idx = min(9, fold_idx + 1)

    return pairs


def compute_manifest_hash(pairs: List[PairAnnotation]) -> str:
    """Compute a deterministic SHA-256 fingerprint for a list of evaluation pair annotations."""
    pair_fingerprints = []
    for p in pairs:
        token = f"{p.pair_id}:{p.image_a}:{p.image_b}:{p.is_genuine}:{p.identity_a}:{p.identity_b}:{p.fold_index}"
        pair_fingerprints.append(token)
    full_manifest_str = "\n".join(sorted(pair_fingerprints))
    return hashlib.sha256(full_manifest_str.encode("utf-8")).hexdigest()


def validate_manifest_splits(pairs: List[PairAnnotation]) -> Dict[str, Any]:
    """Audit evaluation pairs for protocol compliance, fold balance, and cross-fold leakage."""
    total_pairs = len(pairs)
    genuine_pairs = [p for p in pairs if p.is_genuine]
    impostor_pairs = [p for p in pairs if not p.is_genuine]
    duplicate_ids = check_duplicate_pairs(pairs)

    folds = sorted(list({p.fold_index for p in pairs if p.fold_index is not None}))
    fold_summaries = {}
    leakage_violations = {}

    for f in folds:
        fold_pairs = [p for p in pairs if p.fold_index == f]
        f_gen = sum(1 for p in fold_pairs if p.is_genuine)
        f_imp = sum(1 for p in fold_pairs if not p.is_genuine)
        fold_summaries[f] = {"total": len(fold_pairs), "genuine": f_gen, "impostor": f_imp}

        # Check cross-fold data leakage against all remaining folds
        train_pairs = [p for p in pairs if p.fold_index != f]
        has_leak, leaking_ids = check_data_leakage(train_pairs, fold_pairs)
        if has_leak:
            leakage_violations[f] = leaking_ids

    return {
        "total_pairs": total_pairs,
        "genuine_count": len(genuine_pairs),
        "impostor_count": len(impostor_pairs),
        "num_folds": len(folds),
        "folds": fold_summaries,
        "has_duplicates": len(duplicate_ids) > 0,
        "duplicate_count": len(duplicate_ids),
        "has_leakage": len(leakage_violations) > 0,
        "leakage_violations": leakage_violations,
    }


def generate_synthetic_benchmark_fixture(
    num_identities: int = 20,
    images_per_identity: int = 6,
    num_folds: int = 10,
    seed: int = 42,
) -> Tuple[List[PairAnnotation], Dict[str, bytes]]:
    """Synthesize a complete, reproducible 10-fold facial benchmark fixture in memory.

    Guarantees strict scientific integrity:
    - 100% identity-disjoint folds: IdentitySet(Fold_i) ∩ IdentitySet(Fold_j) = ∅ for all i != j.
    - Balanced genuine and impostor pairs within each fold.
    - Zero duplicate image pairings.
    - Highly reliable YuNet detection geometry with identity-differentiated facial features.
    
    Returns:
    - pairs (List[PairAnnotation]): 10-fold identity-disjoint balanced pairs
    - image_store (Dict[str, bytes]): in-memory JPEG byte buffers keyed by image path
    """
    if num_identities < num_folds * 2:
        raise ValueError(
            f"At least {num_folds * 2} identities ({num_folds} folds * 2 identities/fold) are "
            f"required to construct strictly identity-disjoint impostor pairs without cross-fold leakage."
        )

    rng = np.random.RandomState(seed)
    image_store: Dict[str, bytes] = {}
    identity_images: Dict[str, List[str]] = {}

    for i in range(num_identities):
        subject_name = f"subject_{i:03d}"
        identity_images[subject_name] = []

        # Distinct identity visual traits: skin tone, hair, eyebrows, nose, mouth
        tone = int(105 + (i * 13) % 45)
        skin_color = (tone + 20, tone, tone - 20)
        hair_color = (
            int(15 + (i % 4) * 20),
            int(12 + (i % 3) * 15),
            int(10 + (i % 2) * 12),
        )
        eye_r = 7 + (i % 3)
        brow_y = 126 + (i % 3) * 2
        mouth_w = 20 + (i % 4) * 3

        for img_idx in range(images_per_identity):
            img_path = f"{subject_name}/img_{img_idx:02d}.jpg"
            identity_images[subject_name].append(img_path)

            # Canvas with subtle background lighting
            arr = np.full((320, 320, 3), 220, dtype=np.uint8)

            # Head contour (fixed canonical size ensuring 100% reliable YuNet detection)
            cv2.ellipse(arr, (160, 160), (70, 95), 0, 0, 360, skin_color, -1)

            # Hair
            cv2.ellipse(arr, (160, 95), (65, 30), 0, 180, 360, hair_color, -1)

            # Eyebrows
            cv2.line(arr, (120, brow_y), (148, brow_y), hair_color, 3)
            cv2.line(arr, (172, brow_y), (200, brow_y), hair_color, 3)

            # Eyes (canonical interocular distance: 50px, aligned at y=140)
            cv2.circle(arr, (135, 140), eye_r, (25, 25, 25), -1)
            cv2.circle(arr, (185, 140), eye_r, (25, 25, 25), -1)

            # Nose (centered at 160, bridge line down to tip at y=172)
            cv2.line(
                arr,
                (160, 145),
                (160, 172),
                (max(0, skin_color[0] - 30), max(0, skin_color[1] - 30), max(0, skin_color[2] - 30)),
                3,
            )
            cv2.circle(
                arr,
                (160, 172),
                6,
                (max(0, skin_color[0] - 35), max(0, skin_color[1] - 35), max(0, skin_color[2] - 35)),
                -1,
            )

            # Mouth
            cv2.ellipse(arr, (160, 210), (mouth_w, 8), 0, 0, 180, (40, 30, 30), -1)

            # Deterministic, subtle photo-level sensor variation
            img_rng = np.random.RandomState(seed + i * 1000 + img_idx * 17)
            sensor_noise = img_rng.randint(-3, 4, size=arr.shape, dtype=np.int16)
            arr = np.clip(arr.astype(np.int16) + sensor_noise, 0, 255).astype(np.uint8)

            _, enc = cv2.imencode(".jpg", arr)
            image_store[img_path] = enc.tobytes()

    # Assign identities to folds: exactly 2 identities per fold
    identities_list = sorted(list(identity_images.keys()))
    ids_per_fold = len(identities_list) // num_folds
    pairs: List[PairAnnotation] = []

    for fold in range(num_folds):
        fold_ids = identities_list[fold * ids_per_fold : (fold + 1) * ids_per_fold]
        sub_a, sub_b = fold_ids[0], fold_ids[1]

        imgs_a = identity_images[sub_a]
        imgs_b = identity_images[sub_b]

        # 1. Genuine Pairs: balanced pairs for sub_a and sub_b within this fold
        n_gen_per_id = min(3, max(1, len(imgs_a) // 2)) if len(imgs_a) >= 4 else max(1, len(imgs_a) - 1)
        for g in range(n_gen_per_id):
            idx1 = (2 * g) % len(imgs_a)
            idx2 = (2 * g + 1) % len(imgs_a)
            if idx1 == idx2:
                idx2 = (idx1 + 1) % len(imgs_a)
            pairs.append(
                PairAnnotation(
                    pair_id=f"fold_{fold}_gen_{sub_a}_{idx1}_{idx2}",
                    image_a=imgs_a[idx1],
                    image_b=imgs_a[idx2],
                    is_genuine=True,
                    identity_a=sub_a,
                    identity_b=sub_a,
                    fold_index=fold,
                    condition="baseline",
                )
            )
            idx1_b = (2 * g) % len(imgs_b)
            idx2_b = (2 * g + 1) % len(imgs_b)
            if idx1_b == idx2_b:
                idx2_b = (idx1_b + 1) % len(imgs_b)
            pairs.append(
                PairAnnotation(
                    pair_id=f"fold_{fold}_gen_{sub_b}_{idx1_b}_{idx2_b}",
                    image_a=imgs_b[idx1_b],
                    image_b=imgs_b[idx2_b],
                    is_genuine=True,
                    identity_a=sub_b,
                    identity_b=sub_b,
                    fold_index=fold,
                    condition="baseline",
                )
            )

        # 2. Impostor Pairs: strictly between sub_a and sub_b (both belong ONLY to this fold)
        n_imp = 2 * n_gen_per_id
        for g in range(n_imp):
            idx_a = g % len(imgs_a)
            idx_b = (g + 1) % len(imgs_b)
            pairs.append(
                PairAnnotation(
                    pair_id=f"fold_{fold}_imp_{sub_a}_{sub_b}_{g}",
                    image_a=imgs_a[idx_a],
                    image_b=imgs_b[idx_b],
                    is_genuine=False,
                    identity_a=sub_a,
                    identity_b=sub_b,
                    fold_index=fold,
                    condition="baseline",
                )
            )

    return pairs, image_store
