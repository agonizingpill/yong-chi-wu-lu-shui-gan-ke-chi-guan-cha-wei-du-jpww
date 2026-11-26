import os

from sqlalchemy import URL

DB_URL = os.getenv("DATABASE_URL") or URL.create(
    "postgresql+psycopg",
    username=os.getenv("DB_USER", "observer"),
    password=os.getenv("DB_PASSWORD", "demo-swim_class-local"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    database=os.getenv("DB_NAME", "swim_class"),
)
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
JWT_SECRET = os.getenv("JWT_SECRET", "local-swim_class-shadow-panel-signing-key")
SEED_DEMO = os.getenv("SEED_DEMO", "false").lower() == "true"
QUEUE_KEY = "pool:factor:requests"
DEMO_PASSWORD = "Waterline2026!"
