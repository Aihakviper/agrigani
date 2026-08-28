# Development Guide

## Branch workflow

- `main`: reviewed and merged work.
- `mvp-development`: active integration branch.
- Create a short-lived branch from `mvp-development` for each task.
- Do not continue work on the old `Frontend` branch; it contains committed
  conflict markers and is already an ancestor of `main`.

Example:

```powershell
git switch mvp-development
git pull --ff-only origin mvp-development
git switch -c feature/vendor-inventory
```

Keep pull requests focused. Do not commit local databases, secrets, uploaded
media, datasets, training runs, model weights, or Python caches.

## Local checks

```powershell
py -3.11 backend\manage.py check
py -3.11 backend\manage.py test
py -3.11 -m py_compile backend\ml_service\app\main.py
git diff --check
```

Run the complete held-out model evaluation with:

```powershell
py -3.11 evaluation\evaluate_all_classes.py
```

This requires the ignored test dataset under `data/yolo/test` and local YOLO
weights under `runs/classify/models/yolov8/train/weights/best.pt`.

## Database initialization

```powershell
py -3.11 backend\manage.py migrate
py -3.11 backend\manage.py seed_data
py -3.11 backend\manage.py createsuperuser
```

`seed_data` creates or updates the disease/treatment catalogue for the 22
model classes and adds demo vendors.

## Frontend integration rule

Before accepting new visual-design work:

1. Confirm the branch starts from the latest `mvp-development`.
2. Reject any file containing `<<<<<<<`, `=======`, or `>>>>>>>`.
3. Preserve API endpoint names and authentication behaviour.
4. Test login, farmer selection, image upload, result rendering, history,
   disease catalogue, and vendor directory.
5. Test at mobile width and on a low-bandwidth connection.

Search for unresolved markers:

```powershell
rg -n "^(<<<<<<<|=======|>>>>>>>)" frontend
```

## Model-development rule

Treat test data as read-only. Training and tuning must use only train/validation
data. Record dataset version, split, weights, command, metrics, and limitations
for every promoted model.

