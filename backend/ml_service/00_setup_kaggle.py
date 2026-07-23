"""
00_setup_kaggle.py
------------------
Downloads the crop pest & disease dataset from Kaggle.
Requires ~/.kaggle/kaggle.json with your API credentials.

Get your API key from: https://www.kaggle.com/settings -> API -> Create New Token
"""

import os
import sys
import zipfile
from pathlib import Path

DATASET_SLUG = Path("C:\\Users\\HUSSAINI IBRAHIM\\Documents\\agrigani\\backend\\ml_service\\plant_disease")
RAW_DIR = Path("data/raw")
DOWNLOAD_DIR = Path("data/downloads")


def check_kaggle_credentials():
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json.exists():
        print("=" * 60)
        print("ERROR: Kaggle credentials not found.")
        print(f"Expected: {kaggle_json}")
        print()
        print("To fix:")
        print("  1. Go to https://www.kaggle.com/settings")
        print("  2. Click 'API' -> 'Create New Token'")
        print("  3. Move the downloaded kaggle.json to ~/.kaggle/")
        print("  4. Run: chmod 600 ~/.kaggle/kaggle.json")
        print("=" * 60)
        sys.exit(1)
    os.chmod(kaggle_json, 0o600)
    print(f"[OK] Kaggle credentials found at {kaggle_json}")


def download_dataset():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded and extracted
    existing_classes = list(RAW_DIR.iterdir()) if RAW_DIR.exists() else []
    if len(existing_classes) > 5:
        print(f"[SKIP] Dataset already extracted ({len(existing_classes)} class folders found in {RAW_DIR})")
        return

    print(f"[INFO] Downloading dataset: {DATASET_SLUG}")
    import subprocess
    result = subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET_SLUG, "-p", str(DOWNLOAD_DIR)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[ERROR] Download failed:\n{result.stderr}")
        sys.exit(1)
    print("[OK] Download complete.")

    # Find and extract the ZIP
    zips = list(DOWNLOAD_DIR.glob("*.zip"))
    if not zips:
        print("[ERROR] No ZIP file found after download.")
        sys.exit(1)

    zip_path = zips[0]
    print(f"[INFO] Extracting {zip_path.name} -> {RAW_DIR} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(RAW_DIR)
    print("[OK] Extraction complete.")


def audit_classes():
    """Print a summary of discovered class folders."""
    print("\n[INFO] Dataset audit:")
    print("-" * 50)
    classes = sorted([d for d in RAW_DIR.iterdir() if d.is_dir()])
    total_images = 0
    for cls in classes:
        imgs = list(cls.glob("*.jpg")) + list(cls.glob("*.jpeg")) + list(cls.glob("*.png"))
        total_images += len(imgs)
        print(f"  {cls.name:<45} {len(imgs):>5} images")
    print("-" * 50)
    print(f"  {'TOTAL':<45} {total_images:>5} images")
    print(f"  Classes found: {len(classes)}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("  Crop Disease Pipeline - Step 0: Dataset Download")
    print("=" * 60)
    # check_kaggle_credentials()
    download_dataset()
    audit_classes()
    print("[DONE] Dataset ready.")
