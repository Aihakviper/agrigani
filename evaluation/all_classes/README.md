# AgriGani 22-Class Held-Out Evaluation

This report evaluates the active YOLOv8 classification artifact on every image
in `data/yolo/test`. The test split contains 3,448 images across all 22 trained
classes. Predictions are raw top-1 model outputs; no API quality gate or
post-processing is applied.

## Overall results

| Metric | Result |
| --- | ---: |
| Accuracy | 89.39% |
| Macro precision | 88.98% |
| Macro recall | 89.20% |
| Macro F1 | 88.98% |
| Weighted F1 | 89.36% |
| Correct predictions | 3,082 / 3,448 |
| Mean local inference latency | 23.51 ms |
| P95 local inference latency | 29.05 ms |

## Performance by crop

| Crop | Correct | Total | Accuracy |
| --- | ---: | ---: | ---: |
| Cashew | 847 | 881 | 96.14% |
| Cassava | 1,000 | 1,053 | 94.97% |
| Maize | 668 | 779 | 85.75% |
| Tomato | 567 | 735 | 77.14% |

## Main weaknesses

- Tomato leaf blight has 64.48% recall and a 35.52% false-negative rate.
- Tomato leaf curl has 67.63% F1 and a 31.88% false-negative rate.
- Maize leaf blight has 69.86% recall and a 30.14% false-negative rate.
- The largest confusion is maize leaf blight predicted as maize leaf spot
  (38 images).
- Tomato leaf blight and tomato Septoria leaf spot are confused in both
  directions (34 and 31 images).

These results measure performance on the existing held-out split, not on an
independent field dataset. Before retraining, review the largest confusion
groups for duplicate images, label errors, data leakage, weak examples, and
class imbalance.

## Reproduce

```powershell
py -3.11 evaluation\evaluate_all_classes.py
```

The evaluator writes raw predictions, per-class and per-crop metrics, count and
normalized confusion matrices, and a JSON summary into this directory.
