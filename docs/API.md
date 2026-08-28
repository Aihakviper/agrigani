# API Reference

Default Django base URL:

```text
http://127.0.0.1:8000/api/v1
```

Authenticated endpoints expect:

```http
Authorization: Bearer <jwt>
```

## Authentication

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/register/` | Public | Create account and receive JWT |
| POST | `/auth/login/` | Public | Authenticate and receive JWT |
| GET | `/auth/me/` | JWT | Current user |
| POST | `/auth/password-reset/` | Public | Request reset token |
| POST | `/auth/password-reset/confirm/` | Public | Confirm password reset |

## Resources

| Resource | Access | Filters |
| --- | --- | --- |
| `/farmers/` | JWT; owner-scoped | `region_code` |
| `/diseases/` | Public | `category` |
| `/vendors/` | Public | `region_code`, `vendor_type`, `is_verified` |
| `/diagnoses/` | JWT; owner-scoped | farmer, disease, region, date |
| `/diagnoses/statistics/` | Public | none |

The disease and vendor endpoints currently use full model viewsets. This means
their write operations are also public, which is a known security issue and
must be changed before production.

## Submit diagnosis

```http
POST /api/v1/diagnoses/
Authorization: Bearer <jwt>
Content-Type: multipart/form-data
```

Required fields:

- `farmer_id`: an existing farmer owned by the authenticated user
- `image`: JPEG or PNG, maximum 5 MB

Optional fields:

- `location`
- `region_code`
- `latitude`
- `longitude`
- `notes`

Example:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/diagnoses/ `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -F "farmer_id=1" `
  -F "image=@C:\images\leaf.jpg" `
  -F "region_code=NG-KD"
```

## ML service

Default base URL:

```text
http://127.0.0.1:8001
```

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Service metadata |
| GET | `/health` | Model health and supported crops |
| GET | `/model/info` | Framework and all class labels |
| POST | `/predict/` | Predict from an accessible image URL |

Prediction request:

```json
{
  "image_url": "http://127.0.0.1:8000/media/diagnoses/example.jpg",
  "metadata": {
    "location": "Kaduna",
    "region_code": "NG-KD"
  }
}
```

Prediction response includes `disease_name`, `disease_confidence`,
`is_healthy`, `severity`, top predictions, treatment fallback, and model
version.

