# IST Africa Procure-to-Pay System

> Enterprise-grade procurement management system with multi-level approval workflow and AI document processing

## 🚀 Live Demo

- **Backend API**: https://procure-to-pay-backend.onrender.com
- **API Documentation**: https://procure-to-pay-backend.onrender.com/api/docs/

## ✨ Features

- **Multi-level Approval Workflow** - Level 1 → Level 2 approval sequence
- **Role-based Access Control** - Staff, Approver1, Approver2, Finance roles
- **AI Document Processing** - OCR text extraction and PDF parsing
- **Purchase Order Generation** - Automated PO creation from proforma invoices
- **Real-time Dashboard** - Statistics and request tracking
- **Responsive UI** - Modern React TypeScript frontend

## 🛠️ Tech Stack

**Backend**
- Django REST Framework
- PostgreSQL
- JWT Authentication
- AI Processing (OCR, PDF)
- Docker

**Frontend**
- React 18 + TypeScript
- Tailwind CSS
- Framer Motion
- Axios

**Package Management**
- UV (Python package manager)
- npm (Node.js packages)

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- UV package manager

### Backend Setup
```bash
cd backend
uv sync
uv run manage.py migrate
uv run manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🔐 Authentication

Register new users at `/register` or use the deployed backend with existing accounts.

**Test Workflow:**
1. Register as Staff → Create purchase request
2. Register as Approver1 → First level approval
3. Register as Approver2 → Final approval
4. Register as Finance → View approved requests

## 📚 API Documentation

Comprehensive API documentation available at:
- Swagger UI: `/api/docs/`
- OpenAPI Schema: `/api/schema/`

## 🧪 Testing

```bash
# Backend tests
cd backend
uv run manage.py test

# Frontend build
cd frontend
npm run build
npm run type-check
```

## 🚀 Deployment

**Backend**: Deployed on Render.com with PostgreSQL
**Frontend**: Production-ready build available

```bash
cd frontend
./deploy.sh  # Deployment script
```

## 📁 Project Structure

```
Procure-to-Pay/
├── backend/                 # Django REST API
│   ├── authentication/     # User management
│   ├── procurement/         # Core business logic
│   └── core/               # Django settings
├── frontend/               # React TypeScript app
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Route components
│   │   └── utils/          # API configuration
└── README.md
```

## 🏆 Assessment Criteria

✅ Multi-level approval workflow  
✅ AI document processing  
✅ Modern frontend interface  
✅ Security implementation  
✅ Production deployment  
✅ Comprehensive documentation  

---

**Built with UV package manager for Python dependency management**