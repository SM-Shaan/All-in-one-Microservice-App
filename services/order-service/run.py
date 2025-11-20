"""Run Order Service"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Order Service")
    print("=" * 60)
    print("\n📍 Service: http://localhost:8003")
    print("📚 Docs: http://localhost:8003/docs\n")
    print("Press CTRL+C to stop")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
