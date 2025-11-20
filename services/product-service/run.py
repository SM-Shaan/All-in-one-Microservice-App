"""
Simple script to run the Product Service locally
=================================================

Usage:
    python run.py
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Product Service")
    print("=" * 60)
    print()
    print("📍 Service will be available at:")
    print("   • API: http://localhost:8002")
    print("   • Swagger Docs: http://localhost:8002/docs")
    print("   • ReDoc: http://localhost:8002/redoc")
    print()
    print("Press CTRL+C to stop the service")
    print("=" * 60)
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
