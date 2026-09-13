"""
01_data_cleaning.py
-------------------
Cleans the raw dataset:
  1. Removes corrupt / unreadable images
  2. Removes near-duplicate images using perceptual hashing
  3. Validates image dimensions (removes tiny/broken thumbnails)
  4. Produces a cleaning report (CSV + console summary)
  5. Flags severely imbalanced classes for augmentation
"""

import os
import shutil
import hashlib
import csv
from pathlib import Path
from collections import defaultdict

import numpy as np
from PIL import Image, UnidentifiedImageError
import imagehash
from tqdm import tqdm

# ── Configuration ────────────────────────────────────────────────────────────
RAW_DIR = Path("c:\\Users\\HUSSAINI IBRAHIM\\Documents\\agrigani\\backend\\ml_service\\plant_disease")
CLEAN_DIR = Path("data/cleaned")
REPORT_PATH = Path("data/cleaning_report.csv")

MIN_WIDTH = 32          # px — discard images smaller than this
MIN_HEIGHT = 32         # px
HASH_THRESHOLD = 8      # perceptual hash distance ≤ this = near-duplicate
# ─────────────────────────────────────────────────────────────────────────────


def is_valid_image(path: Path) -> tuple[bool, str]:
    """Return (valid, reason). Checks: readable, RGB convertible, minimum size."""
    try:
        with Image.open(path) as img:
            img.verify()           # catches truncated files
    except (UnidentifiedImageError, Exception) as e:
        return False, f"corrupt: {e}"

    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            w, h = img.size
            if w < MIN_WIDTH or h < MIN_HEIGHT:
                return False, f"too small ({w}x{h})"
    except Exception as e:
        return False, f"load error: {e}"

    return True, "ok"


def phash(path: Path):
    try:
        with Image.open(path) as img:
            return imagehash.phash(img.convert("RGB"))
    except Exception:
        return None


def clean_class(src_dir: Path, dst_dir: Path, stats: dict):
    """Process one class folder. Copy clean, unique images to dst_dir."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    images = sorted(
        src_dir.glob("*"),
        key=lambda p: p.name
    )
    images = [p for p in images if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}]

    seen_hashes = {}       # hash -> first filename
    kept = 0
    removed_corrupt = 0
    removed_small = 0
    removed_dup = 0

    for img_path in images:
        valid, reason = is_valid_image(img_path)
        if not valid:
            if "corrupt" in reason or "load error" in reason:
                removed_corrupt += 1
            else:
                removed_small += 1
            stats["removed"].append({"class": src_dir.name, "file": img_path.name, "reason": reason})
            continue

        # Near-duplicate check via perceptual hash
        h = phash(img_path)
        if h is not None:
            dup = False
            for seen_h in seen_hashes:
                if (h - seen_h) <= HASH_THRESHOLD:
                    removed_dup += 1
                    stats["removed"].append({
                        "class": src_dir.name,
                        "file": img_path.name,
                        "reason": f"near-duplicate of {seen_hashes[seen_h]}"
                    })
                    dup = True
                    break
            if dup:
                continue
            seen_hashes[h] = img_path.name

        # Copy clean image
        shutil.copy2(img_path, dst_dir / img_path.name)
        kept += 1

    stats["classes"][src_dir.name] = {
        "original": len(images),
        "kept": kept,
        "removed_corrupt": removed_corrupt,
        "removed_small": removed_small,
        "removed_dup": removed_dup,
    }


def write_report(stats: dict):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["class", "original", "kept", "removed_corrupt", "removed_small", "removed_dup"])
        writer.writeheader()
        for cls, row in sorted(stats["classes"].items()):
            writer.writerow({"class": cls, **row})
    print(f"\n[INFO] Cleaning report saved to {REPORT_PATH}")


def print_summary(stats: dict):
    print("\n" + "=" * 70)
    print("  CLEANING SUMMARY")
    print("=" * 70)
    print(f"  {'Class':<45} {'Orig':>6} {'Kept':>6} {'Corr':>6} {'Small':>6} {'Dup':>6}")
    print("-" * 70)

    total_orig = total_kept = 0
    class_counts = []

    for cls, row in sorted(stats["classes"].items()):
        print(f"  {cls:<45} {row['original']:>6} {row['kept']:>6} "
              f"{row['removed_corrupt']:>6} {row['removed_small']:>6} {row['removed_dup']:>6}")
        total_orig += row["original"]
        total_kept += row["kept"]
        class_counts.append((cls, row["kept"]))

    print("-" * 70)
    print(f"  {'TOTAL':<45} {total_orig:>6} {total_kept:>6}")
    print("=" * 70)
    print(f"\n  Removed: {total_orig - total_kept} images ({(total_orig-total_kept)/max(total_orig,1)*100:.1f}%)")

    # Class imbalance warning
    counts = [c for _, c in class_counts]
    if counts:
        mx, mn = max(counts), min(counts)
        ratio = mx / max(mn, 1)
        print(f"\n  Class imbalance ratio (max/min): {ratio:.1f}x")
        if ratio > 5:
            print("  [WARNING] Severe imbalance detected. Augmentation is strongly recommended.")
            worst = sorted(class_counts, key=lambda x: x[1])[:3]
            print(f"  Smallest classes: {[f'{c}({n})' for c,n in worst]}")
    print()


def main():
    print("=" * 60)
    print("  Crop Disease Pipeline - Step 1: Data Cleaning")
    print("=" * 60)

    if not RAW_DIR.exists():
        print(f"[ERROR] Raw data not found at {RAW_DIR}")
        print("  Run 00_setup_kaggle.py first.")
        raise SystemExit(1)

    class_dirs = sorted([d for d in RAW_DIR.iterdir() if d.is_dir()])
    if not class_dirs:
        print(f"[ERROR] No class subdirectories found in {RAW_DIR}")
        raise SystemExit(1)

    print(f"[INFO] Found {len(class_dirs)} class folders in {RAW_DIR}")
    print(f"[INFO] Output -> {CLEAN_DIR}")
    print(f"[INFO] Hash threshold for near-duplicates: {HASH_THRESHOLD}\n")

    stats = {"removed": [], "classes": {}}

    for cls_dir in tqdm(class_dirs, desc="Cleaning classes"):
        dst = CLEAN_DIR / cls_dir.name
        clean_class(cls_dir, dst, stats)

    write_report(stats)
    print_summary(stats)
    print("[DONE] Cleaned dataset written to", CLEAN_DIR)


if __name__ == "__main__":
    main()
