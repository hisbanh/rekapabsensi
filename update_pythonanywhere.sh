#!/bin/bash

# Script untuk update aplikasi di PythonAnywhere
# Repository: https://github.com/hisbanh/rekapabsensi
# Jalankan dengan: bash update_pythonanywhere.sh

echo "🔄 Starting update process for SIPA Yaumi..."

# Pastikan berada di directory yang benar
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Make sure you're in the project directory."
    echo "   Run: cd rekapabsensi"
    exit 1
fi

# Aktifkan virtual environment
echo "📦 Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found. Please create it first."
    exit 1
fi

# Pull perubahan terbaru dari GitHub
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to pull from GitHub. Check your internet connection or repository access."
    exit 1
fi

# Install/update dependencies
echo "🔧 Installing/updating dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install dependencies."
    exit 1
fi

# Jalankan migrasi database
echo "🗄️ Running database migrations..."
python manage.py migrate

if [ $? -ne 0 ]; then
    echo "❌ Error: Database migration failed."
    exit 1
fi

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to collect static files."
    exit 1
fi

# Check Django configuration
echo "🔍 Checking Django configuration..."
python manage.py check

if [ $? -ne 0 ]; then
    echo "⚠️ Warning: Django configuration check found issues."
fi

echo ""
echo "✅ Update completed successfully!"
echo "🌐 Next steps:"
echo "   1. Go to PythonAnywhere dashboard"
echo "   2. Click 'Web' tab"
echo "   3. Click 'Reload yourusername.pythonanywhere.com'"
echo ""
echo "📊 You can now test your application at:"
echo "   https://yourusername.pythonanywhere.com"