# Procure-to-Pay System

> Modern procurement management platform with automated workflows and intelligent document processing

## 🚀 Live Demo

- **Frontend Application**: https://ist-africa-procumet-o-pay.netlify.app/
- **Backend API**: https://procure-to-pay-backend.onrender.com
- **API Documentation**: https://procure-to-pay-backend.onrender.com/api/docs/

## 🎯 Complete Workflow Implementation

### Procurement Process Flow
1. **Request Submission** → Staff creates purchase request
2. **Proforma Upload** → AI extracts vendor/item data (stays PENDING)
3. **Level 1 Approval** → First approver reviews (still PENDING)
4. **Level 2 Approval** → Final approval triggers automatic PO generation
5. **Receipt Validation** → Upload receipt, AI compares with PO, flags mismatches

## ✨ Features

- **Multi-level Approval Workflow** - Level 1 → Level 2 approval sequence
- **Role-based Access Control** - Staff, Approver1, Approver2, Finance roles
- **AI Document Processing** - OCR text extraction and PDF parsing
- **Purchase Order Generation** - Automated PO creation from proforma invoices
- **Real-time Dashboard** - Statistics and request tracking
- **Responsive UI** - Modern React TypeScript frontend

## 🛠️ Tech Stack

**Backend**
- Django REST Framework 3.14
- PostgreSQL (Production) / SQLite (Development)
- JWT Authentication (SimpleJWT)
- AI Processing: pytesseract (OCR), pdfplumber, PyPDF2
- Docker + Render.com deployment

**Frontend**
- React 18 + TypeScript
- Tailwind CSS + Framer Motion
- Axios + React Router
- Netlify deployment

**AI Document Processing**
- OCR text extraction from images/PDFs
- Regex pattern matching for data extraction
- Automatic PO generation from proforma data
- Receipt validation against purchase orders

**Package Management**
- UV (Modern Python package manager)
- npm (Node.js packages)

## 🏃♂️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- UV package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Backend Setup (Virtual Environment)
```bash
cd backend

# Create and activate virtual environment with UV
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
uv sync

# Setup database
uv run python manage.py migrate

# Create superuser (optional)
uv run python manage.py createsuperuser

# Run development server
uv run python manage.py runserver
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs/

## 🔐 Authentication & Testing

### User Roles & Workflow Testing

**1. Staff User**
- Register with role "staff"
- Create purchase requests
- Upload proforma invoices
- Submit receipts for validation

**2. Level 1 Approver**
- Register with role "approver1"
- Review and approve/reject requests
- First level in approval chain

**3. Level 2 Approver**
- Register with role "approver2"
- Final approval triggers PO generation
- Complete approval workflow

### Complete Test Scenario
```bash
# 1. Staff creates request with proforma
POST /api/procurement/requests/
# → Status: PENDING, proforma data extracted

# 2. Level 1 approver approves
PATCH /api/procurement/requests/{id}/approve/
# → Status: still PENDING (awaiting Level 2)

# 3. Level 2 approver approves
PATCH /api/procurement/requests/{id}/approve/
# → Status: APPROVED, PO auto-generated

# 4. Staff uploads receipt
POST /api/procurement/requests/{id}/submit-receipt/
# → Validates against PO, flags mismatches
```

## 📚 API Documentation

Comprehensive API documentation available at:
- Swagger UI: `/api/docs/`
- OpenAPI Schema: `/api/schema/`

## 🧪 Testing

### Backend Testing
```bash
cd backend

# Run all tests (82 test cases)
uv run python manage.py test

# Run specific test modules
uv run python manage.py test procurement.tests.test_models
uv run python manage.py test procurement.tests.test_views
uv run python manage.py test procurement.tests.test_integration

# Test with coverage
uv run python manage.py test --verbosity=2
```

### Frontend Testing
```bash
cd frontend

# Type checking
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

### API Testing
```bash
# Test complete workflow
cd backend
./test_api_workflow.sh

# Manual API testing
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "staff1", "password": "test123"}'
```

## 🚀 Deployment

### Production Deployment

**Backend**: Render.com + PostgreSQL
- Automatic deployments from GitHub
- Environment variables configured
- PostgreSQL database with connection pooling
- Static files served via WhiteNoise

**Frontend**: Netlify
- Automatic deployments from GitHub
- Environment variables for API endpoints
- Build optimization and CDN distribution

### Environment Setup

**Backend (.env)**
```bash
DEBUG=False
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=procure-to-pay-backend.onrender.com
CORS_ALLOWED_ORIGINS=https://ist-africa-procumet-o-pay.netlify.app
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
```

**Frontend (.env)**
```bash
VITE_API_URL=https://procure-to-pay-backend.onrender.com
VITE_APP_NAME=IST Africa Procure-to-Pay
```

### Local Deployment
```bash
# Backend production setup
cd backend
uv run python manage.py collectstatic
uv run gunicorn core.wsgi:application

# Frontend production build
cd frontend
npm run build
npm run preview
```

## 📁 Project Structure

```
Procure-to-Pay/
├── backend/                           # Django REST API
│   ├── authentication/               # User management & JWT
│   │   ├── models.py                 # UserProfile model
│   │   ├── serializers.py            # Auth serializers
│   │   └── views.py                  # Login/Register endpoints
│   ├── procurement/                   # Core business logic
│   │   ├── models.py                 # PurchaseRequest, Approval, RequestItem
│   │   ├── views.py                  # API endpoints & workflow
│   │   ├── serializers.py            # Data serialization
│   │   ├── document_processor.py     # AI document processing
│   │   ├── permissions.py            # Role-based permissions
│   │   └── tests/                    # Comprehensive test suite
│   ├── core/                         # Django configuration
│   │   ├── settings.py               # Environment-based config
│   │   └── urls.py                   # API routing
│   ├── media/                        # File uploads (proformas, receipts)
│   ├── .env                          # Environment variables
│   ├── pyproject.toml                # UV dependencies
│   └── manage.py                     # Django management
├── frontend/                         # React TypeScript SPA
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   │   ├── RequestDetailsModal.tsx
│   │   │   ├── ApprovalHistory.tsx
│   │   │   └── FileUpload.tsx
│   │   ├── pages/                    # Route components
│   │   │   ├── Dashboard.tsx         # Statistics & overview
│   │   │   ├── Requests.tsx          # Request management
│   │   │   ├── CreateRequest.tsx     # Request creation form
│   │   │   └── Login.tsx             # Authentication
│   │   ├── utils/
│   │   │   ├── api.ts                # Axios configuration
│   │   │   └── auth.ts               # JWT token management
│   │   ├── hooks/                    # Custom React hooks
│   │   └── types/                    # TypeScript definitions
│   ├── package.json                  # npm dependencies
│   └── vite.config.ts                # Build configuration
├── .github/workflows/                # CI/CD pipelines
├── README.md                         # This documentation
└── LICENSE                           # MIT License
```

## 🎯 Key Features

**Workflow Management**
- Multi-level approval process with proper sequencing
- Role-based access control for different user types
- Status tracking throughout the procurement lifecycle
- Comprehensive approval history and audit trail

**Document Processing**
- Intelligent proforma invoice data extraction
- Automatic purchase order generation
- Receipt validation with discrepancy detection
- Support for multiple file formats (PDF, images)

**Modern Architecture**
- RESTful API design with comprehensive endpoints
- Responsive web interface built with React and TypeScript
- Real-time dashboard with procurement statistics
- Secure file upload and management system

**Production Ready**
- Containerized deployment with Docker
- Cloud hosting with automatic scaling
- Comprehensive test suite with high coverage
- Professional API documentation

## 🔗 Links

- **Live Application**: https://ist-africa-procumet-o-pay.netlify.app/
- **API Documentation**: https://procure-to-pay-backend.onrender.com/api/docs/
- **Backend API**: https://procure-to-pay-backend.onrender.com