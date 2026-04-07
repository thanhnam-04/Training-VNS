from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

os.makedirs("uploads", exist_ok=True)

from app.core.database import engine, Base
from app.api.routers import auth, posts

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo DB lúc bắt đầu
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    print("Shutting down...")

app = FastAPI(
    title="Blog API - Mini Project Full",
    description="Chứa CRUD, DB Async (Postgres), JWT Auth, RBAC, Background Task (Dùng cho Day 4-7)",
    version="1.0.0",
    lifespan=lifespan
)

# Thêm CORS để Frontend có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(posts.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
