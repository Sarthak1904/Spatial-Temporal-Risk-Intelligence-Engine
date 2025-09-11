"""Versioned API router."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import analytics, auth, events, health, hotspots, risk, tiles

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(events.router, tags=["events"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(risk.router, tags=["risk"])
api_router.include_router(tiles.router, tags=["tiles"])
api_router.include_router(hotspots.router, tags=["hotspots"])
api_router.include_router(health.router, tags=["health"])
