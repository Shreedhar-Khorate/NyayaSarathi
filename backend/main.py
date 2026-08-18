import os
from pathlib import Path
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analyze, dataset

# Automatically load environment variables from backend/.env if present
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

app = FastAPI(
    title="NyayaSarathi API",
    description="Judicial Case Intelligence & Data-Driven Judgment Success Predictor API",
    version="2.0.0"
)

# CORS Setup: Allow dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # React + Vite default port
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Next.js default port
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(analyze.router)
app.include_router(dataset.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to NyayaSarathi API Server v2. Grounded Judgment Success Predictor active."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
