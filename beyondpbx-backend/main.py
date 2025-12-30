from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import telephony

app = FastAPI(title="FreePBX Moderno")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https?://localhost(:[0-9]+)?"
)

app.include_router(telephony.router)