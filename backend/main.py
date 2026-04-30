from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-20s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)

from db.mongo import connect, disconnect
from routers import jobs, analyze, cv


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🚀 SEEKJOBS BACKEND STARTING ON PORT 8001")
    await connect()
    yield
    await disconnect()


app = FastAPI(title="SeekJobs API", lifespan=lifespan, redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request
import time

@app.middleware("http")
async def debug_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    print(f"DEBUG: {request.method} {request.url.path} -> {response.status_code} ({duration:.2f}s)")
    return response

app.include_router(jobs.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(cv.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
