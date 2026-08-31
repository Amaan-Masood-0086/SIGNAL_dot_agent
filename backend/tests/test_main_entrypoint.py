"""Regression: the uvicorn entrypoint must expose a real ASGI app.

`uvicorn app.main:app` resolves the module-level `app` attribute at import
time. If that attribute is a lazy placeholder (None), uvicorn wraps None and
every request dies with 'NoneType' object is not callable — the test suite
never noticed because it builds apps via the create_app factory.
"""


def test_module_level_app_is_a_real_fastapi_instance():
    from fastapi import FastAPI

    from app import main

    assert isinstance(main.app, FastAPI)


def test_module_level_app_serves_health():
    from fastapi.testclient import TestClient

    from app import main

    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
