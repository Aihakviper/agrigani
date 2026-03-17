# AgriSight Core - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER / FARMER                               │
│              (Web Browser / Mobile App)                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    FRONTEND LAYER                                   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Farmer       │  │  Diagnosis   │  │  History     │            │
│  │ Registration │  │  Submission  │  │  View        │            │
│  │  Form        │  │  (Image)     │  │              │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                     │
│  HTML + CSS + Bootstrap + Vanilla JavaScript                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ REST API (JSON)
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                   DJANGO BACKEND (API LAYER)                        │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    API Endpoints                              │ │
│  │                                                              │ │
│  │  /api/v1/farmers/      → Farmer Management                  │ │
│  │  /api/v1/diseases/     → Disease Catalog                    │ │
│  │  /api/v1/vendors/      → Vendor Directory                   │ │
│  │  /api/v1/diagnoses/    → Main Diagnosis Workflow            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│  ┌──────────────────────────▼────────────────────────────────────┐ │
│  │                  Business Logic Layer                         │ │
│  │                                                              │ │
│  │  • Image Upload & Validation                                │ │
│  │  • Object Storage Integration                               │ │
│  │  • ML Service Communication                                 │ │
│  │  • Disease/Treatment Matching                               │ │
│  │  • Vendor Recommendation                                    │ │
│  │  • Diagnosis Recording                                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Django REST Framework + Custom Services                            │
└───────────┬─────────────────────────┬──────────────┬───────────────┘
            │                         │              │
            │                         │              │
            ▼                         ▼              ▼
┌───────────────────┐   ┌─────────────────────┐   ┌──────────────────┐
│  POSTGRESQL DB    │   │  OBJECT STORAGE     │   │  FASTAPI ML      │
│                   │   │                     │   │  SERVICE         │
│ ┌───────────────┐ │   │  Options:           │   │                  │
│ │ Farmers       │ │   │  • Local (Dev)      │   │ ┌──────────────┐ │
│ │ Diseases      │ │   │  • Supabase         │   │ │ CNN Model    │ │
│ │ Treatments    │ │   │  • Azure Blob       │   │ │ (TensorFlow) │ │
│ │ Vendors       │ │   │  • Cloudflare R2    │   │ └──────────────┘ │
│ │ Diagnoses     │ │   │                     │   │                  │
│ │ Diagnosis     │ │   │  Stores:            │   │  Endpoints:      │
│ │ Vendors       │ │   │  • Crop images      │   │  /predict/       │
│ └───────────────┘ │   │  • Signed URLs      │   │  /health         │
│                   │   │                     │   │  /model/info     │
└───────────────────┘   └─────────────────────┘   └──────────────────┘
```

## Diagnosis Workflow (Detailed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                  STEP-BY-STEP DIAGNOSIS FLOW                        │
└─────────────────────────────────────────────────────────────────────┘

1. USER ACTION
   │
   ├─> User uploads image via web form
   │   (JPEG/PNG, max 5MB)
   │
   └─> Form data: farmer_id, image, location, region_code

2. DJANGO RECEIVES REQUEST
   │
   ├─> POST /api/v1/diagnoses/
   │
   └─> DiagnosisCreateSerializer validates:
       • Image format (JPEG/PNG only)
       • Image size (max 5MB)
       • Farmer exists in database
       
3. IMAGE STORAGE
   │
   ├─> ObjectStorageService.upload_image()
   │
   ├─> Generates unique filename (UUID)
   │
   ├─> Uploads to configured storage backend:
   │   • Local: /media/diagnoses/
   │   • Supabase: Cloud bucket
   │   • Azure/R2: Cloud storage
   │
   └─> Returns public image URL

4. ML SERVICE CALL
   │
   ├─> MLServiceClient.predict_disease()
   │
   ├─> POST to FastAPI: /predict/
   │   {
   │     "image_url": "https://...",
   │     "metadata": {
   │       "location": "...",
   │       "region_code": "..."
   │     }
   │   }
   │
   └─> FastAPI returns:
       {
         "disease_name": "Maize Leaf Blight",
         "disease_confidence": 0.87,
         "treatment_recommendation": {...},
         "ml_model_version": "v1.0"
       }

5. DISEASE LOOKUP/CREATION
   │
   ├─> Search for disease by name in database
   │
   ├─> If found: Use existing disease record
   │
   └─> If not found:
       • Create new Disease record
       • Create Treatment record from ML data
       • Link treatment to disease

6. VENDOR RECOMMENDATION
   │
   ├─> Query vendors by region_code
   │
   ├─> Filter by is_verified=True
   │
   ├─> Select top 5 vendors
   │
   └─> Create DiagnosisVendor links

7. SAVE DIAGNOSIS
   │
   ├─> Create Diagnosis record with:
   │   • farmer_id
   │   • disease_id
   │   • image_url
   │   • confidence_score
   │   • location data
   │   • raw_ml_response (JSON)
   │
   └─> Link recommended vendors

8. RETURN RESPONSE
   │
   └─> DiagnosisSerializer formats complete response:
       {
         "id": 1,
         "farmer_name": "Ibrahim Musa",
         "disease_name": "Maize Leaf Blight",
         "disease_details": {
           "symptoms": "...",
           "treatments": [...]
         },
         "confidence_score": 87.0,
         "image_url": "https://...",
         "recommended_vendors": [...]
       }

9. FRONTEND DISPLAYS
   │
   └─> Shows diagnosis card with:
       • Disease information
       • Confidence level
       • Treatment recommendations
       • Nearby vendors
       • Contact information
```

## Data Flow Diagram

```
┌───────────┐
│   User    │
└─────┬─────┘
      │ 1. Upload Image
      ▼
┌─────────────────────┐
│  Django Backend     │
│  (API Gateway)      │
└──┬────────┬────────┬┘
   │        │        │
   │        │        │ 3. Predict
   │        │        ▼
   │        │   ┌─────────────┐
   │        │   │  FastAPI    │
   │        │   │  ML Service │
   │        │   └─────────────┘
   │        │        │
   │        │        │ 4. Prediction
   │        │        ▼
   │        │   ┌─────────────┐
   │        ├──>│ PostgreSQL  │
   │        │   │  Database   │
   │        │   └─────────────┘
   │        │        │
   │        │        │ 5. Store Diagnosis
   │        │        ▼
   │        │   ┌─────────────┐
   │        └──>│   Object    │
   │ 2. Store│  │   Storage   │
   │         │  └─────────────┘
   │         │
   │         │ 6. Response
   ▼         ▼
┌─────────────────────┐
│  User Interface     │
│  (Diagnosis Result) │
└─────────────────────┘
```

## Deployment Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        PRODUCTION                              │
└────────────────────────────────────────────────────────────────┘

                            ┌─────────────┐
                            │   Users     │
                            └──────┬──────┘
                                   │
                                   │ HTTPS
                                   ▼
                            ┌─────────────┐
                            │  Load       │
                            │  Balancer   │
                            └──────┬──────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
            ┌──────────────┐            ┌──────────────┐
            │  Nginx       │            │  Nginx       │
            │  (Reverse    │            │  (Reverse    │
            │   Proxy)     │            │   Proxy)     │
            └──────┬───────┘            └──────┬───────┘
                   │                           │
                   ▼                           ▼
            ┌──────────────┐            ┌──────────────┐
            │  Gunicorn    │            │  Gunicorn    │
            │  (3 workers) │            │  (3 workers) │
            └──────┬───────┘            └──────┬───────┘
                   │                           │
                   │                           │
                   └──────────┬────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   (Managed DB)  │
                    └─────────────────┘

External Services:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Supabase       │    │  FastAPI ML     │    │  Monitoring     │
│  Storage        │    │  Service        │    │  (Sentry/       │
│  (Images)       │    │  (Separate)     │    │   NewRelic)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────┘

Layer 1: Network
  • HTTPS/TLS encryption
  • Firewall rules
  • DDoS protection (Cloudflare)

Layer 2: Application
  • Django security middleware
  • CORS configuration
  • Rate limiting
  • Input validation

Layer 3: Authentication (Future)
  • JWT tokens
  • Session management
  • Password hashing (PBKDF2)

Layer 4: Data
  • SQL injection prevention (ORM)
  • XSS protection
  • CSRF tokens
  • Encrypted connections

Layer 5: Storage
  • Signed URLs (time-limited)
  • Access control
  • File type validation
  • Size limits (5MB)

Layer 6: Monitoring
  • Error tracking (Sentry)
  • Audit logs
  • Suspicious activity detection
```

## Scalability Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   SCALING STRATEGY                          │
└─────────────────────────────────────────────────────────────┘

Horizontal Scaling:
  Django App Servers ───┬─── Instance 1 (Gunicorn)
                        ├─── Instance 2 (Gunicorn)
                        └─── Instance N (Gunicorn)

Database Scaling:
  PostgreSQL ───┬─── Primary (Read/Write)
                └─── Replicas (Read-only)

Caching Layer:
  Redis ───┬─── Cache frequently accessed data
           ├─── Session storage
           └─── Rate limiting

CDN Layer:
  Cloudflare ───┬─── Static files
                ├─── Image delivery
                └─── DDoS protection

Queue System (Future):
  Celery ───┬─── Background tasks
            ├─── Email notifications
            └─── Heavy processing
```

## Technology Stack

```
Frontend:
  • HTML5
  • CSS3 (Bootstrap)
  • JavaScript (Vanilla)

Backend:
  • Python 3.11
  • Django 4.2
  • Django REST Framework 3.14
  • Gunicorn (WSGI)

Database:
  • PostgreSQL 15

Storage:
  • Supabase / Azure / R2 / Local

ML Service:
  • FastAPI
  • TensorFlow/Keras
  • CNN Model

Infrastructure:
  • Docker
  • Nginx
  • Ubuntu Server

Deployment:
  • Railway / Render / Heroku
  • VPS (DigitalOcean, AWS)

Monitoring:
  • Sentry (Error tracking)
  • PostgreSQL monitoring
  • Application logs
```

---

**This architecture is designed for:**
- ✅ Scalability (horizontal scaling ready)
- ✅ Reliability (fault-tolerant design)
- ✅ Security (multi-layer protection)
- ✅ Performance (caching, CDN, optimization)
- ✅ Maintainability (clear separation of concerns)
