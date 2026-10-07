"""FastAPI main application entrypoint for Q-Catalyst."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router

app = FastAPI(
    title="Q-Catalyst API",
    description="Backend API serving real multimodal scientific artifacts for PETase enzyme engineering triage.",
    version="0.1.0",
)

# CORS Configuration: allow localhost Vite dev server (5173, 3000, etc.) and environment-configured origins
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:8501",
]
if allowed_origins_env:
    for o in allowed_origins_env.split(","):
        if o.strip() and o.strip() not in allowed_origins:
            allowed_origins.append(o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "app": "Q-Catalyst API",
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/api/health",
    }
