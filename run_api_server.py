"""
REST API Server Runner
Main entry point to start the Flask server with SocketIO
"""

import sys
from pathlib import Path

# Add rest-api to path (folder name contains hyphen)
rest_api_path = Path(__file__).parent / "rest-api"
sys.path.insert(0, str(rest_api_path))

# Import must use module name without hyphen
from app import app, socketio  # noqa: E402
from config import settings  # noqa: E402


def main():
    """Start the Flask + SocketIO server"""
    print(f"{settings.api_title} (v{settings.api_version})")
    print(f"Dashboard: http://{settings.api_host}:{settings.api_port}/")
    print(f"API Info:  http://{settings.api_host}:{settings.api_port}/api")
    print(f"Health:    http://{settings.api_host}:{settings.api_port}/health")
    print("WebSocket: Enabled (Real-time monitoring)")
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

