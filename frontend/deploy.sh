#!/bin/bash

# Frontend Deployment Script for IST Africa Procure-to-Pay System

echo "🚀 Starting frontend deployment..."

# Build the project
echo "📦 Building frontend..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "📁 Build files are in the 'dist' directory"
    echo ""
    echo "🌐 To deploy to a static hosting service:"
    echo "   - Netlify: Drag and drop the 'dist' folder"
    echo "   - Vercel: Run 'vercel --prod' in this directory"
    echo "   - GitHub Pages: Copy 'dist' contents to gh-pages branch"
    echo ""
    echo "🔧 Environment Variables needed:"
    echo "   VITE_API_URL=https://procure-to-pay-backend.onrender.com"
else
    echo "❌ Build failed!"
    exit 1
fi