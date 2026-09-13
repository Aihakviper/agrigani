# Crop Pest & Disease Detection Pipeline

End-to-end ML pipeline for the Kaggle dataset:
https://www.kaggle.com/datasets/nirmalsankalana/crop-pest-and-disease-detection

## Models Trained
1. **YOLOv8** — object detection + classification (Ultralytics)
2. **MobileNetV2** — lightweight transfer learning classifier (TensorFlow/Keras)
3. **EfficientNetB0** — accuracy-optimised classifier (TensorFlow/Keras)

## Project Structure
```
crop_disease_pipeline/
├── README.md
├── requirements.txt
├── 00_setup_kaggle.py        # Kaggle API setup + download
├── 01_data_cleaning.py       # Corrupt file removal, deduplication, class audit
├── 02_prepare_dataset.py     # Train/val/test split, YOLO labels, augmentation
├── 03_train_mobilenetv2.py   # MobileNetV2 fine-tuning
├── 04_train_efficientnet.py  # EfficientNetB0 fine-tuning
├── 05_train_yolov8.py        # YOLOv8 classification training
├── 06_evaluate_all.py        # Compare models, confusion matrix, F1 scores
└── 07_predict.py             # Single-image inference with best model
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Kaggle credentials
Place your `kaggle.json` in `~/.kaggle/` then run:
```bash
python 00_setup_kaggle.py
```
Or manually download the dataset ZIP and unzip to `data/raw/`.

### 3. Clean & prepare
```bash
python 01_data_cleaning.py
python 02_prepare_dataset.py
```

### 4. Train all models
```bash
python 03_train_mobilenetv2.py
python 04_train_efficientnet.py
python 05_train_yolov8.py
```

### 5. Evaluate & compare
```bash
python 06_evaluate_all.py
```

### 6. Run prediction on a new image
```bash
python 07_predict.py --image path/to/leaf.jpg
```

## Expected Dataset Structure (after download)
```
data/raw/
├── Corn___Common_Rust/
├── Corn___Gray_Leaf_Spot/
├── Corn___Healthy/
├── Corn___Northern_Leaf_Blight/
├── Rice___Brown_Spot/
├── Rice___Healthy/
├── Rice___Leaf_Blast/
├── Tomato___Bacterial_Spot/
├── Tomato___Early_Blight/
├── Tomato___Healthy/
... (and more classes)
```
