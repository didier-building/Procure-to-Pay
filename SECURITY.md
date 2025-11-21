# 🔒 Security Guidelines for Procure-to-Pay System

## Environment Variables Required for Production

### Required Variables (Production will fail without these):
```bash
SECRET_KEY=your-super-secret-production-key-minimum-50-characters-long
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_secure_database_password
```

### Optional Variables:
```bash
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,*.render.com
DB_HOST=localhost
DB_PORT=5432
```

## Security Checklist

### ✅ Implemented Security Features:
- [x] Environment-based configuration
- [x] No hard-coded secrets in code
- [x] Secure secret key validation
- [x] Database credential validation
- [x] .env file gitignored
- [x] CORS configuration
- [x] Security headers for production
- [x] JWT token authentication

### 🔒 Deployment Security Steps:

1. **Generate Production Secret Key:**
   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```

2. **Set Environment Variables in Production:**
   - Never commit secrets to git
   - Use platform-specific secrets management
   - Rotate keys regularly

3. **Database Security:**
   - Use strong passwords
   - Enable SSL connections
   - Restrict database access

### ⚠️ Security Notes:

- The `.env` file contains development secrets only
- Production secrets must be set via hosting platform
- All database credentials are validated at startup
- Application will fail fast if required secrets are missing

## Platform-Specific Setup:

### Railway:
```bash
railway variables set SECRET_KEY=your-secret-key
railway variables set DB_PASSWORD=your-db-password
```

### Render:
Set in Environment Variables section of dashboard

### Fly.io:
```bash
fly secrets set SECRET_KEY=your-secret-key
fly secrets set DB_PASSWORD=your-db-password
```

## Demo Users (Development Only):

**⚠️ Change these in production!**

- Admin: admin/admin123
- Staff: staff1/staff123  
- Approver 1: approver1/approver123
- Approver 2: approver2/approver123
- Finance: finance/finance123