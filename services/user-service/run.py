"""
Simple script to run the User Service locally
==============================================

Usage:
    python run.py
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting User Service")
    print("=" * 60)
    print()
    print("📍 Service will be available at:")
    print("   • API: http://localhost:8001")
    print("   • Swagger Docs: http://localhost:8001/docs")
    print("   • ReDoc: http://localhost:8001/redoc")
    print()
    print("Press CTRL+C to stop the service")
    print("=" * 60)
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
