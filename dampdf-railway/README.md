# DamPDF - Railway Deployment

## 🚂 Deployed on Railway

This is the Railway-optimized version of DamPDF API.

### Features
- ✅ Image Compression (JPG, PNG, WEBP)
- ✅ PDF Compression
- ✅ DOCX to PDF Conversion
- ✅ XLSX to PDF Conversion
- ✅ Redis Session Management
- ✅ Real-time Processing Status
- ✅ File Download with Expiration

### API Endpoints
- `GET /` - API Information
- `GET /health` - Health Check
- `GET /docs` - Interactive API Documentation
- `POST /api/v1/files/upload` - Upload File
- `POST /api/v1/process/start` - Start Processing
- `GET /api/v1/process/status/{session_id}` - Get Processing Status
- `GET /api/v1/download/file/{session_id}` - Download Processed File

### Environment Variables
Set these in Railway dashboard:
- `DEBUG=False`
- `SECRET_KEY=your-secret-key`
- `MAX_FILE_SIZE_MB=50`
- `BACKEND_CORS_ORIGINS=["https://your-frontend-domain.com"]`

### Deployment
This app is configured to deploy automatically on Railway when pushed to the main branch.
