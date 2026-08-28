# Architecture

## System context

```text
Browser frontend
      |
      | HTTP/JSON and multipart uploads
      v
Django REST API -----------------> SQLite (development)
      |                            PostgreSQL (recommended production)
      |
      +--------------------------> Object storage / local media
      |
      | image URL + metadata
      v
FastAPI ML service
      |
      v
YOLOv8 22-class classifier
```

## Components

### Frontend

The client is static HTML, Bootstrap, CSS, and JavaScript under `frontend/`.
It provides authentication, farmer management, diagnosis upload, history,
disease information, and vendor-directory screens.

The current frontend files contain unresolved Git conflict markers. See
[Known issues](KNOWN_ISSUES.md) before editing or deploying them.

### Django API

The Django project lives under `backend/`.

- `agrigani_core/core/models.py`: Farmer, Disease, Treatment, Vendor,
  Diagnosis, and DiagnosisVendor models.
- `agrigani_core/api/views.py`: REST endpoints and diagnosis orchestration.
- `agrigani_core/api/serializers.py`: request and response validation.
- `agrigani_core/api/storage_service.py`: local or object-storage uploads.
- `agrigani_core/api/ml_service.py`: FastAPI client.
- `agrigani_core/api/crop_catalog.py`: metadata for all 22 trained classes.

### ML service

`backend/ml_service/app/main.py` exposes health, model-information, and
prediction endpoints. `app/model.py` loads the YOLO weights once and separates
model loading, inference, response formatting, treatment fallback, and
severity formatting.

The active artifact is resolved from several candidate locations, with the
normal local path:

```text
runs/classify/models/yolov8/train/weights/best.pt
```

Weights and datasets are deliberately ignored by Git.

## Diagnosis sequence

1. The user authenticates and selects a farmer they own.
2. The browser sends a multipart request containing `farmer_id` and an image.
3. Django validates the request and ownership.
4. The storage service saves the image and returns an accessible URL.
5. Django sends that URL and location metadata to FastAPI.
6. FastAPI downloads the image and runs YOLO classification.
7. Django maps the model label to the 22-class crop catalogue.
8. Django stores the diagnosis, confidence, model version, and raw response.
9. Up to five verified vendors in the same region are attached.
10. The API returns disease details, treatments, and vendor referrals.

## Data relationships

```text
User 1---* Farmer 1---* Diagnosis *---0..1 Disease 1---* Treatment
                              |
                              *---* Vendor (through DiagnosisVendor)
```

## Supported crops

- Cashew: 5 classes
- Cassava: 5 classes
- Maize: 7 classes
- Tomato: 5 classes

The complete class list is returned by `GET /model/info` on the ML service.

