"""FastAPI application entry point for the ULPF backend."""

from time import monotonic

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, inspect, select, text

from ulpf import LogProcessingPipeline

from api.database import Base, SessionLocal, engine
from api.db_mapping_store import DatabaseMappingStore
from api.db_models import DBEvent, DBSourceMapping, DBUser
from api.auth import hash_password
from api.routers import analytics, auth, chat, events, ingest, mappings

_started_at = monotonic()

Base.metadata.create_all(bind=engine)


def _upgrade_existing_sqlite() -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table in ("events", "source_mappings"):
            columns = {column["name"] for column in inspector.get_columns(table)}
            if "user_id" not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER"))


def _seed_demo_users() -> None:
    demo_users = [
        ("demo@ulpf.local", "Demo Analyst", "demo12345"),
        ("alice@ulpf.local", "Alice Chen", "alice12345"),
        ("bob@ulpf.local", "Bob Singh", "bob12345"),
        ("carol@ulpf.local", "Carol Rivera", "carol12345"),
        ("dave@ulpf.local", "Dave Okafor", "dave12345"),
    ]
    with SessionLocal() as db:
        for email, name, password in demo_users:
            if db.scalar(select(DBUser).where(DBUser.email == email)) is None:
                db.add(DBUser(email=email, display_name=name, password_hash=hash_password(password)))
        db.commit()
        owner = db.scalar(select(DBUser).where(DBUser.email == demo_users[0][0]))
        if owner is not None:
            db.query(DBEvent).filter(DBEvent.user_id.is_(None)).update({"user_id": owner.id}, synchronize_session=False)
            db.query(DBSourceMapping).filter(DBSourceMapping.user_id.is_(None)).update({"user_id": owner.id}, synchronize_session=False)
            db.commit()


_upgrade_existing_sqlite()
_seed_demo_users()

app = FastAPI(title="ULPF Engine API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = LogProcessingPipeline()
mapping_store = DatabaseMappingStore(SessionLocal, user_id=1)
pipeline.mapping_store = mapping_store
app.state.pipeline = pipeline
app.state.mapping_store = mapping_store
app.state.pipelines = {1: pipeline}


def get_pipeline(user_id: int) -> LogProcessingPipeline:
    if user_id not in app.state.pipelines:
        user_pipeline = LogProcessingPipeline()
        user_pipeline.mapping_store = DatabaseMappingStore(SessionLocal, user_id=user_id)
        app.state.pipelines[user_id] = user_pipeline
    return app.state.pipelines[user_id]


app.state.get_pipeline = get_pipeline

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(events.router)
app.include_router(mappings.router)
app.include_router(analytics.router)


@app.get("/health")
def health() -> dict[str, object]:
    database_status = "ok"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            active_mappings = db.scalar(
                select(func.count())
                .select_from(DBSourceMapping)
                .where(DBSourceMapping.is_approved.is_(True))
            ) or 0
    except Exception:
        database_status = "error"
        active_mappings = 0
    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "database": database_status,
        "active_mappings": active_mappings,
        "uptime_seconds": round(monotonic() - _started_at, 3),
    }
