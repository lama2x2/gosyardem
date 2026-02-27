from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import setup_admin
from app.database import engine, Base
from app.routes import requests, users, proofs, request_types


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Платформа помощи гражданам",
    description="API для сервиса отчётов о городских проблемах. Фронт — Telegram-бот.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(requests.router, prefix="/api/requests", tags=["requests"])
app.include_router(proofs.router, prefix="/api/proofs", tags=["proofs"])
app.include_router(request_types.router, prefix="/api/request-types", tags=["request-types"])

admin = setup_admin(app)

@app.get("/")
async def root():
    return {"message": "Платформа помощи гражданам API", "docs": "/docs", "admin": "/admin"}
