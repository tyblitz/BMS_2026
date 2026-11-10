"""
BMS Web Application Launcher
Starts the unified FastAPI + Vue 3 application on http://localhost:8000
"""
import uvicorn
import os
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

if __name__ == "__main__":
    print("=" * 65)
    print("  DepEd Budget Monitoring System (BMS 2026)")
    print("  Unified Web Application (FastAPI + Vue 3)")
    print("=" * 65)
    print("  Application URL: http://localhost:8000")
    print("  Swagger API Docs: http://localhost:8000/docs")
    print("  Default Admin:   username='admin', password='Admin123!'")
    print("=" * 65)
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, app_dir="backend")

