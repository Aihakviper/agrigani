# AgriGani

AgriGani is an AI-assisted crop diagnosis MVP for cashew, cassava, maize, and
tomato. A browser frontend submits crop images to a Django REST API, which
stores the diagnosis and calls a separate FastAPI/YOLOv8 classification
service. The backend also provides treatment metadata and regional vendor
referrals.

## Current status

- 22 trained plant-condition classes across four crops.
- 3,448-image held-out evaluation completed.
- Overall test accuracy: **89.39%**.
- Cashew accuracy: **96.14%**.
- Cassava accuracy: **94.97%**.
- Maize accuracy: **85.75%**.
- Tomato accuracy: **77.14%**.
- JWT authentication and farmer-scoped diagnosis history are implemented.
- The frontend currently contains unresolved merge markers and must be cleaned
  before it is treated as release-ready.
- The vendor feature is currently a regional directory/referral system, not a
  transactional marketplace.

## Repository layout

```text
agrigani/
|-- backend/
|   |-- agrigani_core/       Django models and REST API
|   |-- config/              Django settings and root routes
|   |-- ml_service/          Training pipeline and FastAPI inference service
|   `-- manage.py
|-- frontend/                Static HTML, CSS, and JavaScript client
|-- evaluation/              Reproducible model evaluations and reports
|-- models/                  Historical model artifacts and training summaries
`-- docs/                    Architecture, development, API, and project status
```

## Start locally

Requirements:

- Python 3.11
- A local copy of the YOLO weights at
  `runs/classify/models/yolov8/train/weights/best.pt`
- Node is optional; the frontend can be served by any static file server

Create and activate a virtual environment, then install both dependency sets:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m pip install -r backend\ml_service\requirements.txt
```

Copy the environment template:

```powershell
Copy-Item backend\.env.example backend\.env
```

Initialize Django:

```powershell
py -3.11 backend\manage.py migrate
py -3.11 backend\manage.py seed_data
py -3.11 backend\manage.py runserver 127.0.0.1:8000
```

Start the ML service in a second terminal:

```powershell
cd backend\ml_service
py -3.11 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Serve the frontend only after resolving the documented conflict markers:

```powershell
cd frontend
py -3.11 -m http.server 5500
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Development guide](docs/DEVELOPMENT.md)
- [API reference](docs/API.md)
- [Known issues and roadmap](docs/KNOWN_ISSUES.md)
- [22-class evaluation](evaluation/all_classes/README.md)

## Safety

Predictions are decision support, not confirmed diagnoses. Users should inspect
multiple plants and consult an agricultural extension professional before
applying pesticides or removing crops.

