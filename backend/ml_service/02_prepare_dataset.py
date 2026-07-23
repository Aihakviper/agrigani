"""
02_prepare_dataset.py
---------------------
Prepares the cleaned data for training:
  1. Stratified train / val / test split  (70 / 15 / 15)
  2. Generates augmented copies for under-represented classes
  3. Writes Keras ImageDataGenerator-compatible folder structure
  4. Writes YOLO classification dataset.yaml  (for ultralytics yolo cls)
  5. Saves label->index mapping as data/class_names.txt
"""

import os
import random
import shutil
from pathlib import Path
from collections import Counter

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# ── Configuration ────────────────────────────────────────────────────────────
CLEAN_DIR  = Path("data/cleaned")
SPLIT_DIR  = Path("data/split")       # Keras-style: split/train/ClassName/
YOLO_DIR   = Path("data/yolo")        # YOLO-cls:    yolo/train/ClassName/
CLASS_FILE = Path("data/class_names.txt")
YAML_PATH  = Path("data/yolo_dataset.yaml")

TRAIN_RATIO = 0.70
VAL_RATIO   = 0.15
TEST_RATIO  = 0.15

# Augment minority classes until they reach at least this many samples
MIN_SAMPLES_PER_CLASS = 300

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
# ─────────────────────────────────────────────────────────────────────────────

SPLITS = ["train", "val", "test"]
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


# ── Augmentation helpers ─────────────────────────────────────────────────────

def augment_image(img: Image.Image) -> Image.Image:
    """Apply a random combination of augmentations."""
    ops = random.sample([
        "flip_h", "flip_v", "rotate", "brightness",
        "contrast", "sharpness", "blur", "crop"
    ], k=random.randint(2, 4))

    for op in ops:
        if op == "flip_h":
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif op == "flip_v" and random.random() < 0.3:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        elif op == "rotate":
            img = img.rotate(random.uniform(-30, 30), expand=False, fillcolor=(0, 0, 0))
        elif op == "brightness":
            img = ImageEnhance.Brightness(img).enhance(random.uniform(0.6, 1.4))
        elif op == "contrast":
            img = ImageEnhance.Contrast(img).enhance(random.uniform(0.7, 1.3))
        elif op == "sharpness":
            img = ImageEnhance.Sharpness(img).enhance(random.uniform(0.5, 2.0))
        elif op == "blur" and random.random() < 0.3:
            img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 1.5)))
        elif op == "crop":
            w, h = img.size
            margin_x = int(w * 0.1)
            margin_y = int(h * 0.1)
            left   = random.randint(0, margin_x)
            top    = random.randint(0, margin_y)
            right  = w - random.randint(0, margin_x)
            bottom = h - random.randint(0, margin_y)
            img = img.crop((left, top, right, bottom)).resize((w, h), Image.LANCZOS)
    return img


# ── Core helpers ─────────────────────────────────────────────────────────────

def collect_images(cls_dir: Path) -> list[Path]:
    return [p for p in cls_dir.iterdir() if p.suffix.lower() in IMG_EXTS]


def split_class(images: list[Path]) -> dict[str, list[Path]]:
    """Stratified split: returns dict with keys train/val/test."""
    n = len(images)
    if n < 3:
        return {"train": images, "val": [], "test": []}

    train_imgs, temp = train_test_split(images, test_size=(1 - TRAIN_RATIO), random_state=SEED)
    rel_val = VAL_RATIO / (VAL_RATIO + TEST_RATIO)
    val_imgs, test_imgs = train_test_split(temp, test_size=(1 - rel_val), random_state=SEED)
    return {"train": train_imgs, "val": val_imgs, "test": test_imgs}


def copy_images(images: list[Path], dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in images:
        shutil.copy2(src, dst_dir / src.name)


def augment_to_min(train_dir: Path, cls_name: str):
    """Generate augmented copies in train_dir until MIN_SAMPLES_PER_CLASS."""
    existing = [p for p in train_dir.iterdir() if p.suffix.lower() in IMG_EXTS]
    need = MIN_SAMPLES_PER_CLASS - len(existing)
    if need <= 0:
        return 0

    augmented = 0
    sources = existing.copy()
    counter = 0
    while augmented < need:
        src = random.choice(sources)
        try:
            with Image.open(src) as img:
                aug = augment_image(img.convert("RGB"))
            aug_name = f"aug_{counter:05d}_{src.stem}.jpg"
            aug.save(train_dir / aug_name, "JPEG", quality=92)
            augmented += 1
            counter += 1
        except Exception:
            pass
    return augmented


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Crop Disease Pipeline - Step 2: Prepare Dataset")
    print("=" * 60)

    if not CLEAN_DIR.exists():
        print(f"[ERROR] Cleaned data not found at {CLEAN_DIR}")
        print("  Run 01_data_cleaning.py first.")
        raise SystemExit(1)

    class_dirs = sorted([d for d in CLEAN_DIR.iterdir() if d.is_dir()])
    class_names = [d.name for d in class_dirs]
    print(f"[INFO] {len(class_names)} classes found")

    # Save label map
    CLASS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CLASS_FILE, "w") as f:
        for i, name in enumerate(class_names):
            f.write(f"{i}\t{name}\n")
    print(f"[INFO] Class map saved -> {CLASS_FILE}")

    # ── Split and copy ───────────────────────────────────────────────────────
    print("\n[INFO] Splitting into train / val / test ...")
    split_counts = {s: Counter() for s in SPLITS}

    for cls_dir in tqdm(class_dirs, desc="Splitting"):
        images = collect_images(cls_dir)
        splits = split_class(images)
        for split, imgs in splits.items():
            dst = SPLIT_DIR / split / cls_dir.name
            copy_images(imgs, dst)
            # Mirror for YOLO
            yolo_dst = YOLO_DIR / split / cls_dir.name
            copy_images(imgs, yolo_dst)
            split_counts[split][cls_dir.name] = len(imgs)

    # ── Augmentation on training set ─────────────────────────────────────────
    print("\n[INFO] Augmenting under-represented training classes ...")
    total_aug = 0
    for cls_name in tqdm(class_names, desc="Augmenting"):
        train_dir = SPLIT_DIR / "train" / cls_name
        n_aug = augment_to_min(train_dir, cls_name)
        if n_aug > 0:
            # Mirror augmented files to YOLO train dir too
            aug_files = [p for p in train_dir.iterdir() if p.name.startswith("aug_")]
            for f in aug_files:
                dst = YOLO_DIR / "train" / cls_name / f.name
                if not dst.exists():
                    shutil.copy2(f, dst)
        total_aug += n_aug

    print(f"[INFO] Total augmented images generated: {total_aug}")

    # ── YOLO YAML ────────────────────────────────────────────────────────────
    yaml_content = f"""# Crop Pest & Disease Detection - YOLO Classification Dataset
path: {YOLO_DIR.resolve()}
train: train
val: val
test: test

nc: {len(class_names)}
names:
"""
    for name in class_names:
        yaml_content += f"  - {name}\n"

    with open(YAML_PATH, "w") as f:
        f.write(yaml_content)
    print(f"[INFO] YOLO yaml saved -> {YAML_PATH}")

    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SPLIT SUMMARY")
    print("=" * 60)
    for split in SPLITS:
        total = sum(split_counts[split].values())
        print(f"  {split.upper():<8}: {total:>6} images across {len(class_names)} classes")
    print("=" * 60)
    print("\n[DONE] Dataset prepared.")
    print(f"  Keras split  -> {SPLIT_DIR}")
    print(f"  YOLO dataset -> {YOLO_DIR}")


if __name__ == "__main__":
    main()
