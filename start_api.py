"""
Script de démarrage de l'API Agrivision
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Démarrage de l'API Agrivision")
    print("📖 Documentation disponible sur: http://localhost:8000/docs")
    print("🔗 Interface Swagger: http://localhost:8000/redoc")
    
    uvicorn.run(
        "api:app",  # Import string instead of app object
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )