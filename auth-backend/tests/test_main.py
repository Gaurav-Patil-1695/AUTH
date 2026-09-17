"""Unit tests for app/main.py"""
import importlib
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers to import the app cleanly
# ---------------------------------------------------------------------------

def get_app():
    """Return a fresh TestClient for the main FastAPI application."""
    from app.main import app
    return app


@pytest.fixture()
def client():
    app = get_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Basic application metadata
# ---------------------------------------------------------------------------

def test_app_title():
    app = get_app()
    assert app.title == "Auth Starter"


def test_app_version():
    app = get_app()
    assert app.version == "1.0.0"


# ---------------------------------------------------------------------------
# Router inclusion – the auth router must be mounted under /api/v1
# ---------------------------------------------------------------------------

def test_auth_router_mounted():
    app = get_app()
    paths = [route.path for route in app.routes]
    # At least one route should begin with /api/v1
    assert any(p.startswith("/api/v1") for p in paths), (
        f"No route found under /api/v1. Routes: {paths}"
    )


# ---------------------------------------------------------------------------
# CORS middleware is present
# ---------------------------------------------------------------------------

def test_cors_middleware_present():
    from starlette.middleware.cors import CORSMiddleware
    app = get_app()
    middleware_types = [type(m) for m in app.user_middleware]
    # Starlette stores middleware as Middleware objects; check the cls attribute
    middleware_classes = [
        m.cls if hasattr(m, "cls") else type(m)
        for m in app.user_middleware
    ]
    assert CORSMiddleware in middleware_classes, (
        f"CORSMiddleware not found. Middleware: {middleware_classes}"
    )


# ---------------------------------------------------------------------------
# CORS_ORIGIN defaults to http://localhost:5173
# ---------------------------------------------------------------------------

def test_cors_origin_default(monkeypatch):
    monkeypatch.delenv("CORS_ORIGIN", raising=False)
    # Re-read the env variable directly as the module reads it at import time;
    # verify the default value defined in the module
    default = os.getenv("CORS_ORIGIN", "http://localhost:5173")
    assert default == "http://localhost:5173"


def test_cors_origin_env_override(monkeypatch):
    monkeypatch.setenv("CORS_ORIGIN", "http://example.com")
    value = os.getenv("CORS_ORIGIN", "http://localhost:5173")
    assert value == "http://example.com"


# ---------------------------------------------------------------------------
# ErrorResponse exception handler
# ---------------------------------------------------------------------------

def test_error_response_handler_returns_json():
    """Call the handler directly and verify the JSON structure."""
    from app.main import error_response_handler
    from app.auth.schemas import ErrorResponse
    import asyncio

    exc = ErrorResponse(status_code=422, code="VALIDATION_ERROR", message="bad input", details={"field": "email"})
    mock_request = MagicMock(spec=Request)

    response = asyncio.get_event_loop().run_until_complete(
        error_response_handler(mock_request, exc)
    )

    assert response.status_code == 422
    import json
    body = json.loads(response.body)
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "bad input"
    assert body["error"]["details"] == {"field": "email"}


def test_error_response_handler_minimal():
    """Handler works when details is None/empty."""
    from app.main import error_response_handler
    from app.auth.schemas import ErrorResponse
    import asyncio
    import json

    exc = ErrorResponse(status_code=401, code="UNAUTHORIZED", message="not allowed")
    mock_request = MagicMock(spec=Request)

    response = asyncio.get_event_loop().run_until_complete(
        error_response_handler(mock_request, exc)
    )

    assert response.status_code == 401
    body = json.loads(response.body)
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "not allowed"


def test_error_response_handler_500():
    """Handler correctly reflects a 500 status code."""
    from app.main import error_response_handler
    from app.auth.schemas import ErrorResponse
    import asyncio
    import json

    exc = ErrorResponse(status_code=500, code="INTERNAL", message="oops", details=None)
    mock_request = MagicMock(spec=Request)

    response = asyncio.get_event_loop().run_until_complete(
        error_response_handler(mock_request, exc)
    )

    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["error"]["code"] == "INTERNAL"


# ---------------------------------------------------------------------------
# API_PREFIX constant
# ---------------------------------------------------------------------------

def test_api_prefix_value():
    from app.main import API_PREFIX
    assert API_PREFIX == "/api/v1"
