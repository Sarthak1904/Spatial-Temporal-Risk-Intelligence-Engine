"""FastAPI application entrypoint."""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.rate_limit import limiter

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.app_debug)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}),
)
app.add_middleware(SlowAPIMiddleware)
app.include_router(api_router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
