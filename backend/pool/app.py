from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from . import auth, cohorts, form_routes, report_routes, survey_routes
from .database import initialize
from .middlewares import correlate, prevent_stale_session, reject_integrity_conflict
from .settings import REDIS_URL, SEED_DEMO


@asynccontextmanager
async def startup(_app):
    initialize()
    if SEED_DEMO:
        from scripts.seed_demo import seed
        try:
            seed()
        except Exception:
            logging.getLogger(__name__).exception("Demo seed failed")
    yield


app = FastAPI(title="芦湾教研 · 课池观察", lifespan=startup)
app.middleware("http")(prevent_stale_session)
app.middleware("http")(correlate)
app.add_exception_handler(IntegrityError, reject_integrity_conflict)

for module in (auth, cohorts, form_routes, report_routes, survey_routes):
    app.include_router(module.router)


@app.get("/health")
def health(db: auth.Db):
    try:
        db.execute(text("SELECT 1"))
        Redis.from_url(REDIS_URL, socket_connect_timeout=1, socket_timeout=1).ping()
    except (RedisError, SQLAlchemyError) as exc:
        raise HTTPException(503, "数据库或消息队列未就绪。") from exc
    return {"status": "ok", "database": "postgres", "queue": "redis"}
