"""
REST API Server Runner
Main entry point to start the Flask server with SocketIO
"""

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(_SRC_DIR))

from web import app, settings, socketio  # noqa: E402


def main():
    """Start the Flask + SocketIO server"""
    display_host = "127.0.0.1"
    display_port = 8080
    print(f"{settings.api_title} (v{settings.api_version})")
    print(f"Dashboard: http://{display_host}:{display_port}/")
    print(f"API Info:  http://{display_host}:{display_port}/api")
    print(f"Health:    http://{display_host}:{display_port}/health")
    print("WebSocket: Disabled (Socket.IO polling)")
    print("Press CTRL+C to stop the server")

    socketio.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        debug=settings.api_reload,
        allow_unsafe_werkzeug=True,  # For development only
    )


if __name__ == "__main__":
    main()
