from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from core.config import AppConfig
from core.engine import DetectionEngine


def create_app(engine: DetectionEngine, config: AppConfig) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["ENGINE"] = engine
    app.config["APP_CONFIG"] = config

    @app.get("/")
    def dashboard():
        return render_template("index.html", config=config)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/status")
    def status():
        return jsonify(engine.get_status())

    @app.get("/api/events")
    def events():
        limit = request.args.get("limit", default=20, type=int)
        limit = max(1, min(limit, 100))
        return jsonify({"events": engine.get_recent_events(limit)})

    return app

