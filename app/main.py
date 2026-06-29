from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base
from app.routers import jobs
from app.routers.auth import router as auth_router
from app.routers.schedule import router as schedule_router
from app.services.scheduler import reload_schedules_from_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Job Application Automator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(auth_router)
app.include_router(schedule_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup_event():
    reload_schedules_from_db()
