from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.database import get_db
from app.main import app


def test_health_and_openapi_without_database():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response = client.get("/openapi.json")
        assert response.status_code == 200
        paths = response.json()["paths"]
        for resource in ("creators", "guides", "comments"):
            assert {"get", "post"} <= paths[f"/{resource}"].keys()
            assert {"get", "patch", "delete"} <= paths[f"/{resource}/{{record_id}}"].keys()
        assert "post" in paths["/imports/bilibili/videos"]


def test_readiness_when_database_is_unavailable():
    class UnavailableDatabase:
        def execute(self, _statement):
            raise OperationalError("connection", {}, Exception("unavailable"))

    app.dependency_overrides[get_db] = lambda: UnavailableDatabase()
    try:
        with TestClient(app) as client:
            response = client.get("/health/ready")
            assert response.status_code == 503
            assert response.json() == {"detail": "Database is not ready"}
    finally:
        app.dependency_overrides.clear()
