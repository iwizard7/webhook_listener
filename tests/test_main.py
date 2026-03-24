import hashlib
import hmac
import json
import sqlite3

from main import create_app


def _client(tmp_path, secret=""):
    app = create_app(
        {
            "TESTING": True,
            "WEBHOOK_DB_PATH": str(tmp_path / "test.db"),
            "WEBHOOK_SECRET": secret,
        }
    )
    return app.test_client(), app.config["WEBHOOK_DB_PATH"]


def test_healthz_ok(tmp_path):
    client, _ = _client(tmp_path)
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_webhook_persists_event(tmp_path):
    client, db_path = _client(tmp_path)
    response = client.post("/webhook", json={"text": "hello"})

    assert response.status_code == 202
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT payload_json FROM webhook_events ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row is not None
    assert json.loads(row[0]) == {"text": "hello"}


def test_webhook_rejects_non_json(tmp_path):
    client, _ = _client(tmp_path)
    response = client.post("/webhook", data="not-json", content_type="text/plain")

    assert response.status_code == 400


def test_webhook_validates_signature(tmp_path):
    secret = "topsecret"
    client, _ = _client(tmp_path, secret=secret)

    body = b'{"text":"signed"}'
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    response = client.post(
        "/webhook",
        data=body,
        content_type="application/json",
        headers={"X-Hub-Signature-256": f"sha256={signature}"},
    )

    assert response.status_code == 202


def test_webhook_rejects_bad_signature(tmp_path):
    client, _ = _client(tmp_path, secret="topsecret")
    response = client.post(
        "/webhook",
        json={"text": "bad"},
        headers={"X-Hub-Signature-256": "sha256=deadbeef"},
    )

    assert response.status_code == 401
