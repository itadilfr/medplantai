from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routers import plants, compounds, health, disease

app = FastAPI(
    title="MedPlant AI API",
    version="1.1.0",
    description="Backend API for the MedPlant AI medicinal-plant research platform."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production to the deployed app domain(s).
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()
    # v6 automatically starts a background enrichment pass for the 100 starter plants.
    # The UI remains usable while NCBI / GBIF / PubChem metadata are cached locally.
    if __import__("os").getenv("AUTO_ENRICH_SEED", "true").lower() == "true":
        import asyncio
        asyncio.create_task(plants.enrich_all_background())

app.include_router(health.router, prefix="/api")
app.include_router(plants.router, prefix="/api")
app.include_router(compounds.router, prefix="/api")
app.include_router(disease.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "name": "MedPlant AI API",
        "version": "1.1.0",
        "docs": "/docs",
        "status": "running"
    }
