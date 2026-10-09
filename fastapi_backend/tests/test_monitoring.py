from unittest import mock

from models import RequestLog


def test_requests_are_logged_with_route_pattern_and_duration(client, auth_headers, test_card, db_session):
    response = client.get("/payments/", headers=auth_headers)
    assert "x-response-time-ms" in response.headers

    row = db_session.query(RequestLog).filter_by(path="/payments/").one()
    assert (row.service, row.method, row.status_code) == ("fastapi", "GET", 200)
    assert row.duration_ms >= 0


def test_route_pattern_is_logged_not_the_raw_id(client, auth_headers, test_card, db_session):
    client.get("/payments/12345", headers=auth_headers)  # 404, but the route is /payments/{payment_id}
    row = db_session.query(RequestLog).one()
    assert row.path == "/payments/{payment_id}"
    assert row.status_code == 404


def test_failed_auth_is_logged_and_health_checks_are_not(client, db_session):
    client.get("/payments/")  # no token
    client.get("/health")
    rows = db_session.query(RequestLog).all()
    assert [(r.path, r.status_code) for r in rows] == [("/payments/", 401)]


def test_an_unhandled_error_is_recorded_with_its_message(client, auth_headers, db_session):
    from fastapi.testclient import TestClient

    from main import app

    crashing = TestClient(app, raise_server_exceptions=False)
    with mock.patch("sqlalchemy.orm.Query.all", side_effect=RuntimeError("db exploded")):
        response = crashing.get("/payments/", headers=auth_headers)
    assert response.status_code == 500
    row = db_session.query(RequestLog).filter_by(status_code=500).one()
    assert "RuntimeError: db exploded" in row.error


def test_a_failing_metrics_write_never_breaks_the_request(client, auth_headers, test_card):
    with mock.patch("monitoring._store", side_effect=RuntimeError("table missing")):
        assert client.get("/payments/", headers=auth_headers).status_code == 200