# 🚀 Render Deployment Guide

## Automatic Deployment (Recommended)

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Connect to Render
1. Go to [render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository: `didier-building/Procure-to-Pay`
5. Render will auto-detect the `render.yaml` configuration

### 3. Environment Variables (Set in Render Dashboard)
Render will auto-generate most variables, but verify these:

**Required:**
- `SECRET_KEY` - Auto-generated ✅
- `DATABASE_URL` - Auto-generated from PostgreSQL service ✅
- `ALLOWED_HOSTS` - Auto-set to your Render domain ✅

**Optional:**
- `DEBUG=False` (auto-set)
- `PYTHON_VERSION=3.11.5`

## Manual Deployment Alternative

If you prefer manual setup:

### 1. Create PostgreSQL Database
- Service Name: `procure-to-pay-db`
- Plan: Starter (Free)

### 2. Create Web Service  
- Service Name: `procure-to-pay`
- Environment: Python
- Build Command: `./build.sh`
- Start Command: `uv run gunicorn core.wsgi:application`
- Plan: Starter (Free)

### 3. Set Environment Variables
```
DATABASE_URL=[from PostgreSQL service]
SECRET_KEY=[generate secure key]
DEBUG=False
ALLOWED_HOSTS=[your-app-name].onrender.com
```

## Expected URLs

After deployment:
- **Main App**: `https://procure-to-pay.onrender.com`
- **Admin**: `https://procure-to-pay.onrender.com/admin/`
- **API**: `https://procure-to-pay.onrender.com/api/procurement/api/requests/`
- **API Docs**: `https://procure-to-pay.onrender.com/api/docs/` (when added)

## Post-Deployment Steps

1. **Create Demo Users**:
   ```bash
   # From Render shell or locally with production DATABASE_URL
   python manage.py create_demo_data
   ```

2. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

3. **Test API**:
   ```bash
   curl https://procure-to-pay.onrender.com/api/token/ \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"username":"staff1","password":"staff123"}'
   ```

## Troubleshooting

### Build Failures
- Check Python version compatibility
- Verify all dependencies in `pyproject.toml`
- Check build logs in Render dashboard

### Runtime Issues  
- Check environment variables are set
- Verify DATABASE_URL connection
- Check application logs in Render

### SSL/Security Issues
- Ensure `SECURE_SSL_REDIRECT = True`
- Verify `ALLOWED_HOSTS` includes your domain
- Check CORS settings for frontend

## Monitoring

- **Logs**: Available in Render dashboard
- **Metrics**: CPU, Memory, Response time
- **Health Checks**: Automatic ping monitoring
- **Alerts**: Configure in Render settings

## Next Steps After Deployment

1. ✅ Verify public URL works
2. ✅ Test API endpoints  
3. ✅ Add frontend application
4. ✅ Implement remaining features incrementally
5. ✅ Set up monitoring and logging

Your application will auto-deploy on every git push to main! 🚀