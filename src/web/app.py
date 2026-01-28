"""
Flask Application with SocketIO for Real-time IoT Dashboard.

This file wires together:
- web routes (UI + basic health/info)
- feature routes (ingest, DB browse/export, metrics)
- background flow (DB writer)
"""

import atexit
import logging
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from .config import settings
from .extensions import socketio
from .feature import db_api, ingest
from .flows import db_writer
from .web_routes import bp as web_bp
from .web_socket import register_handlers as register_socket_handlers


_BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(_BASE_DIR / "static"),
    template_folder=str(_BASE_DIR / "templates"),
)

app.config["SECRET_KEY"] = settings.api_key

# Enable CORS
CORS(app, resources={r"/*": {"origins": settings.allow_origins}})

# Silence Werkzeug request logs (127.0.0.1 - - [...]) unless errors
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# Init SocketIO
socketio.init_app(app)

# Routes
app.register_blueprint(web_bp)
app.register_blueprint(ingest.bp)
app.register_blueprint(db_api.bp)

# WebSocket events
register_socket_handlers()


@app.before_request
def _ensure_flows_started():
    db_writer.start_once()


atexit.register(db_writer.stop)


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"status": "error", "message": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"status": "error", "message": "Internal server error", "detail": str(e)}), 500
