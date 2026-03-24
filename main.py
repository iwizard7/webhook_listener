"""Webhook listener with signature validation and SQLite persistence."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request


def _init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at TEXT NOT NULL,
                source TEXT,
                event_id TEXT,
                remote_addr TEXT,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _is_valid_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    received_signature = signature_header.split("=", 1)[1]
    expected_signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received_signature, expected_signature)


def _save_event(db_path: str, payload: dict[str, Any], remote_addr: str | None) -> int:
    received_at = datetime.now(timezone.utc).isoformat()
    source = request.headers.get("User-Agent")
    event_id = request.headers.get("X-GitHub-Delivery")
    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO webhook_events (received_at, source, event_id, remote_addr, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (received_at, source, event_id, remote_addr, json.dumps(payload, ensure_ascii=False)),
        )
        connection.commit()
        return int(cursor.lastrowid)


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        WEBHOOK_DB_PATH=os.getenv("WEBHOOK_DB_PATH", "data/webhooks.db"),
        WEBHOOK_SECRET=os.getenv("WEBHOOK_SECRET", ""),
    )

    if test_config:
        app.config.update(test_config)

    _init_db(app.config["WEBHOOK_DB_PATH"])

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    @app.get("/healthz")
    def healthz():
        try:
            with sqlite3.connect(app.config["WEBHOOK_DB_PATH"]) as connection:
                connection.execute("SELECT 1")
            return jsonify({"status": "ok", "db": "ok"}), 200
        except sqlite3.Error:
            app.logger.exception("Healthcheck failed")
            return jsonify({"status": "error", "db": "unavailable"}), 503

    @app.post("/")
    @app.post("/webhook")
    def webhook():
        if not request.is_json:
            return jsonify({"error": "content-type must be application/json"}), 400

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "invalid JSON payload"}), 400

        secret = app.config.get("WEBHOOK_SECRET", "")
        if secret:
            signature = request.headers.get("X-Hub-Signature-256")
            if not _is_valid_signature(secret, request.get_data(), signature):
                return jsonify({"error": "invalid signature"}), 401

        event_db_id = _save_event(app.config["WEBHOOK_DB_PATH"], payload, request.remote_addr)
        return jsonify({"status": "received", "event_id": event_db_id}), 202

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
