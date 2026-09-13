# AgriGani Core - Backend

AI-powered agricultural diagnosis platform for crop and livestock disease detection with treatment recommendations and vendor referrals.

## 🌾 Overview

AgriGani Core is a Django REST API backend that provides:

- **AI Disease Diagnosis**: Image-based disease detection using ML models
- **Treatment Recommendations**: Evidence-based treatment guidance
- **Vendor Referrals**: Location-based agro-medicine dealer recommendations
- **Diagnosis History**: Complete tracking of farmer diagnoses
- **Multi-Storage Support**: Local, Supabase, Azure Blob, or Cloudflare R2

## 🏗️ Architecture

```
Frontend (HTML/JS/Bootstrap)
         ↓
Django REST API
         ↓
    ┌────┴────┐
    ↓         ↓
PostgreSQL  Object Storage  ←→  FastAPI ML Service
```

## 📋 Features

### Core Functionality
- ✅ Farmer registration and management
- ✅ Image upload with validation (JPEG/PNG, max 5MB)
- ✅ Disease detection via ML service integration
- ✅ Treatment recommendation engine
- ✅ Location-based vendor matching
- ✅ Diagnosis history and analytics

### API Endpoints

#### Farmers
- `GET /api/v1/farmers/` - List farmers
- `POST /api/v1/farmers/` - Create farmer
- `GET /api/v1/farmers/{id}/` - Get farmer details
- `PUT/PATCH /api/v1/farmers/{id}/` - Update farmer
- `DELETE /api/v1/farmers/{id}/` - Delete farmer

#### Diseases
- `GET /api/v1/diseases/` - List diseases
- `POST /api/v1/diseases/` - Create disease
- `GET /api/v1/diseases/{id}/` - Get disease details
- `GET /api/v1/diseases/{id}/treatments/` - Get disease treatments

#### Vendors
- `GET /api/v1/vendors/` - List vendors
- `POST /api/v1/vendors/` - Create vendor
- `GET /api/v1/vendors/{id}/` - Get vendor details

#### Diagnoses (Main Workflow)
- `POST /api/v1/diagnoses/` - **Submit diagnosis** (image upload)
- `GET /api/v1/diagnoses/` - List diagnoses
- `GET /api/v1/diagnoses/{id}/` - Get diagnosis details
- `GET /api/v1/diagnoses/statistics/` - Get statistics

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- (Optional) Docker & Docker Compose

### Option 1: Docker Setup (Recommended)

```bash
# Clone repository
cd agrigani-backend

# Create environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Start services
docker-compose up -d

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Access API at http://localhost:8000/api/v1/
# Access Admin at http://localhost:8000/admin/
```

### Option 2: Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Setup database
# Make sure PostgreSQL is running
createdb agrigani_db

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# API available at http://localhost:8000/api/v1/
```

## 📊 Database Schema

### Tables
1. **Farmers** - User information and farm details
2. **Diseases** - Crop/livestock diseases catalog
3. **Treatments** - Treatment protocols per disease
4. **Vendors** - Agro-dealers and veterinary clinics
5. **Diagnoses** - Diagnosis records with ML results
6. **DiagnosisVendors** - Vendor recommendations per diagnosis

### ER Diagram
```
Farmer ─┬─< Diagnosis >── Disease ──< Treatment
        │                    
        │               
        └───────────────────< Vendor
                            (via DiagnosisVendor)
```

## 🔧 Configuration

### Environment Variables

Key settings in `.env`:

```env
# Database
DB_NAME=agrigani_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Object Storage (choose one)
OBJECT_STORAGE_TYPE=local  # Options: local, supabase, azure, r2

# FastAPI ML Service
FASTAPI_ML_SERVICE_URL=http://localhost:8001
```

### Storage Backends

#### Local Storage (Development)
```env
OBJECT_STORAGE_TYPE=local
BASE_URL=http://localhost:8000
```

#### Supabase Storage
```env
OBJECT_STORAGE_TYPE=supabase
OBJECT_STORAGE_URL=https://your-project.supabase.co
OBJECT_STORAGE_KEY=your-supabase-anon-key
OBJECT_STORAGE_BUCKET=agrigani-images
```

#### Azure Blob Storage
```env
OBJECT_STORAGE_TYPE=azure
OBJECT_STORAGE_URL=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...
OBJECT_STORAGE_BUCKET=agrigani-images
```

#### Cloudflare R2
```env
OBJECT_STORAGE_TYPE=r2
OBJECT_STORAGE_URL=https://account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_ACCOUNT_ID=your-account-id
```

## 🧪 Testing the API

### Create a Farmer
```bash
curl -X POST http://localhost:8000/api/v1/farmers/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Ibrahim Musa",
    "phone_number": "08012345678",
    "location": "Rigasa, Kaduna",
    "region_code": "NG-KD"
  }'
```

### Submit Diagnosis (with image)
```bash
curl -X POST http://localhost:8000/api/v1/diagnoses/ \
  -F "farmer_id=1" \
  -F "image=@/path/to/maize-leaf.jpg" \
  -F "location=Rigasa, Kaduna" \
  -F "region_code=NG-KD"
```

### Get Diagnoses
```bash
# All diagnoses
curl http://localhost:8000/api/v1/diagnoses/

# For specific farmer
curl http://localhost:8000/api/v1/diagnoses/?farmer_id=1

# Statistics
curl http://localhost:8000/api/v1/diagnoses/statistics/
```

## 🔌 ML Service Integration

The backend expects a FastAPI ML service at the configured URL (`FASTAPI_ML_SERVICE_URL`).

### Expected ML Service Contract

**Endpoint:** `POST /predict/`

**Request:**
```json
{
  "image_url": "https://storage.example.com/image.jpg",
  "metadata": {
    "location": "Kaduna",
    "region_code": "NG-KD"
  }
}
```

**Response:**
```json
{
  "disease_name": "Maize Leaf Blight",
  "disease_confidence": 0.87,
  "treatment_recommendation": {
    "medicine": "Mancozeb Fungicide",
    "dosage": "2.5kg per hectare",
    "application_method": "Foliar spray",
    "frequency": "Every 7-10 days",
    "precautions": "Avoid spraying during rain"
  },
  "vendor_info": [],
  "ml_model_version": "v1.0"
}
```

**Note:** If ML service is unavailable, the system falls back to a mock service for testing.

## 📦 Project Structure

```
agrigani-backend/
├── config/                 # Django settings
│   ├── __init__.py
│   ├── settings.py        # Main settings
│   ├── urls.py            # Root URL config
│   └── wsgi.py
├── agrigani_core/
│   ├── core/              # Core models
│   │   ├── models.py      # Database models
│   │   ├── admin.py       # Admin interface
│   │   └── apps.py
│   └── api/               # REST API
│       ├── views.py       # ViewSets
│       ├── serializers.py # DRF serializers
│       ├── urls.py        # API routing
│       ├── storage_service.py  # Object storage
│       └── ml_service.py  # ML integration
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🛠️ Management Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver

# Run tests
python manage.py test
```

## 📈 Deployment

### Production Checklist

1. **Security**
   - Change `DJANGO_SECRET_KEY`
   - Set `DEBUG=False`
   - Configure `ALLOWED_HOSTS`
   - Enable HTTPS

2. **Database**
   - Use production PostgreSQL
   - Enable backups
   - Configure connection pooling

3. **Storage**
   - Use cloud storage (not local)
   - Configure CDN for images

4. **Performance**
   - Set up Gunicorn workers
   - Configure Nginx reverse proxy
   - Enable caching (Redis)
   - Set up monitoring

### Deployment Platforms

- **Railway/Render**: One-click deployment
- **Heroku**: Procfile included
- **AWS/Azure/GCP**: Full control
- **DigitalOcean**: Droplet + managed DB

## 🔐 Security Features

- File upload validation (type, size)
- CORS configuration
- SQL injection prevention (Django ORM)
- XSS protection
- CSRF protection
- Signed URLs for object storage

## 📊 Monitoring & Analytics

### Available Statistics
- Total diagnoses
- Disease distribution
- Regional analysis
- Farmer activity
- Vendor utilization

Access via: `GET /api/v1/diagnoses/statistics/`

## 🤝 Integration with Frontend

The backend is designed to work with:
- HTML/CSS/Bootstrap frontend
- Mobile apps (React Native, Flutter)
- Third-party integrations

All endpoints return JSON responses compatible with modern frontend frameworks.

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
sudo service postgresql status

# Check connection
psql -U postgres -d agrigani_db
```

### ML Service Not Available
- System automatically falls back to mock service
- Check `FASTAPI_ML_SERVICE_URL` in `.env`
- Verify ML service is running

### Image Upload Failed
- Check file size < 5MB
- Verify file type (JPEG/PNG)
- Check storage configuration
- Verify media directory permissions

## 📝 License

This project is part of Aihak Agrotech's AgriGani platform.

## 👥 Authors

- **Ahmad Hamza Isah** - Aihak Agrotech

## 🔗 Related Projects

- **AgriGani ML Service** - FastAPI inference service
- **AgriGani Frontend** - Web interface
- **AgriGani Intelligence** - Analytics platform (future)

---

For questions or support, contact: support@aihakagrotech.com
