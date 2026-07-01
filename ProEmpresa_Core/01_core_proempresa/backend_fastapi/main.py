import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router
from app.routes.cliente import router as cliente_router
from app.routes.personal import router as personal_router

app = FastAPI(
    title="Core ProEmpresa",
    description="API para portal interno, app de fuerza de ventas y app cliente.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173")
origins = [o.strip() for o in origins_env.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cliente_router)
app.include_router(personal_router)

@app.get("/")
def root():
    return {"name": "Core ProEmpresa", "status": "online"}

@app.get("/health")
def health():
    return {"status": "healthy"}
