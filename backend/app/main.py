"""SupportIQ FastAPI application entrypoint."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config.settings import settings
from app.api.v1.router import api_router
from app.database.session import engine, close_mongo_client

logger = logging.getLogger("supportiq")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SupportIQ (%s)", settings.app_env)
    yield
    await engine.dispose()
    await close_mongo_client()
    logger.info("SupportIQ shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="AI-Powered Customer Support Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "code": "validation_error"},
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.app_env,
        "llm_provider": settings.llm_provider,
    }


@app.get("/")
async def root():
    return {
        "message": "Welcome to SupportIQ API",
        "docs": "/docs",
        "health": "/health",
        "api": settings.app_api_prefix,
    }


app.include_router(api_router, prefix=settings.app_api_prefix)