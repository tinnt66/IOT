"""
REST API Module
Flask server with SocketIO for receiving IoT sensor data and real-time monitoring
"""

from .app import app, socketio
from .config import settings

__version__ = "2.0.0"
__all__ = ['app', 'socketio', 'settings']

