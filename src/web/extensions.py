"""
Extension instances (SocketIO, etc.).

Kept separate to avoid circular imports between app setup and feature modules.
"""

from flask_socketio import SocketIO

from .config import settings


socketio = SocketIO(
    cors_allowed_origins=settings.allow_origins,
    transports=["polling"],
    allow_upgrades=False,
    logger=False,
    engineio_logger=False,
)
