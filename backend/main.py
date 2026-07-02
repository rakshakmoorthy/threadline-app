from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health import router as health_router
from routes.conditions import router as conditions_router
from routes.opportunities import router as opportunities_router

app = FastAPI(
    title="Threadline API",
    description="AI-powered market intelligence for adaptive fashion",
    version="1.0.0"
)

# CORS — allows React frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(conditions_router)
app.include_router(opportunities_router)

@app.get("/")
def root():
    return {
        "service": "Threadline API",
        "version": "1.0.0",
        "docs": "/docs"
    }