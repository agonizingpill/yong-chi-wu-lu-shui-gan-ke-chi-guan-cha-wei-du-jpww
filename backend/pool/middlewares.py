import logging
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .audit import request_id

logger = logging.getLogger("swim.audit")


async def correlate(request: Request, call_next):
    correlation = uuid4().hex
    token = request_id.set(correlation)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation
        logger.info("%s %s %s %s", correlation, request.method, request.url.path, response.status_code)
        return response
    finally:
        request_id.reset(token)


async def prevent_stale_session(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/auth", "/waves", "/forms")):
        response.headers["Cache-Control"] = "no-store"
    return response


async def reject_integrity_conflict(_request: Request, _error: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "编号或匿名券已使用，请刷新后再试。"})
