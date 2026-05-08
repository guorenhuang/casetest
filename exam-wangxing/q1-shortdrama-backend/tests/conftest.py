import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fixture_secret")
os.environ.setdefault("STRIPE_SIGNATURE_TOLERANCE_SECONDS", "300")
os.environ.setdefault("APPLE_SHARED_SECRET", "apple_shared_mock_secret")


@pytest.fixture
async def client(tmp_path, monkeypatch):
    dbfile = tmp_path / "t.db"
    monkeypatch.setenv("DATABASE_PATH", str(dbfile))

    import importlib

    import app.db

    importlib.reload(app.db)
    from app.db import init_db

    init_db()
    import app.main

    importlib.reload(app.main)
    app = app.main.app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
