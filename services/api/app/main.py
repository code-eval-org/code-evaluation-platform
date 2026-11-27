import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.app.routes import health_router, router

app = FastAPI(
    title="Project 4 Submission API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(health_router)
