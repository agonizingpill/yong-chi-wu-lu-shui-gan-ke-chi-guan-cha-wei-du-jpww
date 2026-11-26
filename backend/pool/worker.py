import logging
from pathlib import Path
import time

from redis import Redis
from sqlalchemy import text

from .database import open_session
from .report_control import do_pending
from .settings import QUEUE_KEY, REDIS_URL

logger = logging.getLogger("pool.worker")
beat = Path("/tmp/pool-beat")


def main():
    logging.basicConfig(level=logging.INFO)
    queue = Redis.from_url(REDIS_URL, socket_timeout=4, socket_connect_timeout=3)
    while True:
        try:
            with open_session() as db:
                db.execute(text("SELECT 1"))
                has_work = do_pending(db)
            queue.ping()
            beat.touch()
            if not has_work:
                queue.brpop(QUEUE_KEY, timeout=3)
        except Exception:
            logger.exception("Worker dependency or sampler failed; durable candidate retained")
            time.sleep(4)


if __name__ == "__main__":
    main()
