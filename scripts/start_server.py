"""
Script to start the FastAPI server.
"""

import uvicorn
import sys
from pathlib import Path

if __name__ == "__main__":
    try:
        print("Starting Trust Gateway API server...")
        print("Server will be available at: http://localhost:8443")
        print("Press Ctrl+C to stop the server")
        uvicorn.run(
            "gateway.main:app",
            host="0.0.0.0",
            port=8443,
            log_level="info",
            use_colors=True,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Failed to start server: {str(e)}", file=sys.stderr)
        sys.exit(1)

