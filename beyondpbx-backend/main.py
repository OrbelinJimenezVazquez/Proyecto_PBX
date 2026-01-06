from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import telephony, asternic  
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="BeyondPBX")

# Configuración de CORS desde variables de entorno
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Métodos específicos en lugar de "*"
    allow_headers=["Content-Type", "Authorization", "Accept"],  # Headers específicos
)

app.include_router(telephony.router)
app.include_router(asternic.router)
@app.get("/")
def read_root():
    return {"message": "BeyondPBX API - Running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "freepbx-api"}