# 🚀 Procure-to-Pay System

A comprehensive procurement management system built with Django REST Framework, featuring multi-level approval workflows, document processing with AI, and role-based access control.

## 🎯 Project Overview

This system handles the complete procurement workflow:
- **Staff** create purchase requests with proforma uploads
- **Multi-level approvers** review and approve/reject requests
- **Automated PO generation** upon final approval
- **Receipt validation** with AI-powered comparison
- **Finance team** access via web interface

## 🏗️ Architecture

### Backend (Django + DRF)
- Django 5.2.8 with REST Framework
- JWT Authentication
- PostgreSQL Database
- File handling for documents
- AI-powered document processing

### Frontend (React)
- Role-based dashboard
- Responsive design
- File upload interface
- Real-time status updates

### Infrastructure
- Docker containerization
- Production deployment ready
- CI/CD pipeline support

## 📋 Current Implementation Status

### ✅ Completed Features
- [x] Core Django project structure
- [x] Database models (PurchaseRequest, Approval, RequestItem)
- [x] Basic API endpoints with ViewSets
- [x] JWT authentication configuration
- [x] Admin interface
- [x] Docker foundation
- [x] Database migrations

### 🚧 In Progress Features
- [ ] User Profile & Role system
- [ ] Complete API endpoints
- [ ] Document processing (AI/OCR)
- [ ] Frontend React application
- [ ] Docker Compose setup
- [ ] Security enhancements
- [ ] API documentation
- [ ] Production deployment

## 🔑 Key Models

### PurchaseRequest
```python
- title: CharField(max_length=255)
- description: TextField
- amount: DecimalField
- status: PENDING/APPROVED/REJECTED
- proforma: FileField (upload_to='proformas/')
- purchase_order: FileField (upload_to='purchase_orders/')
- receipt: FileField (upload_to='receipts/')
- created_by: ForeignKey(User)
- final_approved_by: ForeignKey(User)
```

### Approval (Two-Level System)
```python
- request: ForeignKey(PurchaseRequest)
- approver: ForeignKey(User)
- level: IntegerField (1 or 2)
- approved: BooleanField (True/False/None)
- comment: TextField
```

### RequestItem
```python
- request: ForeignKey(PurchaseRequest)
- name: CharField
- quantity: PositiveIntegerField
- unit_price: DecimalField
```

## 🌐 API Endpoints

### Authentication
- `POST /api/token/` - Get JWT token
- `POST /api/token/refresh/` - Refresh token

### Purchase Requests
- `GET /api/procurement/api/requests/` - List requests
- `POST /api/procurement/api/requests/` - Create request
- `GET /api/procurement/api/requests/{id}/` - Request details
- `PATCH /api/procurement/api/requests/{id}/` - Update request
- `PATCH /api/procurement/api/requests/{id}/approve/` - Approve request
- `PATCH /api/procurement/api/requests/{id}/reject/` - Reject request
- `POST /api/procurement/api/requests/{id}/submit-receipt/` - Submit receipt

## 👥 User Roles & Permissions

### Staff
- Create purchase requests
- View own requests
- Update pending requests
- Submit receipts for approved requests

### Approver Level 1
- View all pending requests
- Approve/reject requests (first level)
- Add comments to approvals

### Approver Level 2
- Final approval authority
- Can approve after Level 1 approval
- Triggers automatic PO generation

### Finance
- View all approved requests
- Access financial reports
- File management capabilities

## 🔄 Approval Workflow

```mermaid
graph TD
    A[Staff Creates Request] --> B[Status: PENDING]
    B --> C[Level 1 Approver Reviews]
    C --> D{Approved?}
    D -->|No| E[Status: REJECTED]
    D -->|Yes| F[Level 2 Approver Reviews]
    F --> G{Final Approved?}
    G -->|No| E
    G -->|Yes| H[Status: APPROVED]
    H --> I[Auto Generate PO]
    I --> J[Receipt Submission Available]
```

## 🤖 AI Document Processing

### Proforma Processing
- Extract vendor details
- Parse line items and prices
- Store metadata for PO generation

### Automatic PO Generation
- Triggered on final approval
- Uses extracted proforma data
- Generates formatted PO document

### Receipt Validation
- Compare items/prices with PO
- Validate vendor information
- Flag discrepancies automatically

### Technologies Used
- `pytesseract` - OCR processing
- `pdfplumber` - PDF text extraction
- `PyPDF2` - PDF manipulation
- OpenAI API integration (planned)

## 🐳 Docker Setup

### Development
```bash
# Build and run
docker build -t procure-to-pay .
docker run -p 8000:8000 procure-to-pay
```

### Production (Docker Compose)
```bash
# Start all services
docker-compose up --build

# Services included:
# - Django application
# - PostgreSQL database
# - Redis (for caching/tasks)
# - Nginx (reverse proxy)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for frontend)

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd Procure-to-Pay

# Backend setup
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver

# Frontend setup (separate terminal)
cd frontend
npm install
npm start
```

### Environment Variables
```bash
# .env file
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
OPENAI_API_KEY=your-openai-key
```

## 🔒 Security Features

- JWT token authentication
- Role-based access control
- CORS configuration
- File upload validation
- SQL injection protection
- XSS protection headers

## 📖 API Documentation

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- Postman Collection: Available in `/docs/`

## 🌍 Deployment

### Production URL
**Live Demo:** [Coming Soon - Will be deployed to AWS EC2/Render]

### Deployment Options
- AWS EC2 with Docker
- Render.com
- Fly.io
- Railway
- DigitalOcean Droplet

## 🧪 Testing

```bash
# Run tests
uv run python manage.py test

# Coverage report
coverage run --source='.' manage.py test
coverage report
```

## 📝 Development Roadmap

### Phase 1: Core Backend (Current)
- ✅ Models and API structure
- 🚧 User roles system
- 🚧 Complete endpoint testing

### Phase 2: Document Processing
- 🔲 Proforma text extraction
- 🔲 PO auto-generation
- 🔲 Receipt validation AI

### Phase 3: Frontend
- 🔲 React application
- 🔲 Role-based UI
- 🔲 File upload interface

### Phase 4: Production
- 🔲 Docker Compose setup
- 🔲 Security hardening
- 🔲 Public deployment

## 👨‍💻 Technical Assessment Completion

This project is being developed as part of the IST Africa Full Stack Python/Django Developer assessment. The system demonstrates:
## 📞 Support

For technical questions during development hours, use the IST Africa app chat system.

- **Complex business logic** with multi-level approvals
- **AI integration** for document processing
- **Production-ready architecture** with Docker
- **Security best practices** and role-based access
- **Modern frontend** with responsive design

**Assessment Deadline:** November 26th, 2025
**Repository:** https://github.com/didier-building/Procure-to-Pay

## 📞 Support

For technical questions during development hours, use the IST Africa app chat system.

---

**Built with ❤️ for IST Africa Technical Assessment**
