"""
api/index.py — Vercel serverless entry point for CORRUGATE IQ.
"""
import sys
import os

# Ensure the root project directory is on sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app import app


class VercelWSGIMiddleware:
    """
    Normalizes PATH_INFO and SCRIPT_NAME when Vercel rewrites requests
    through /api/index so Flask matches the original user routes cleanly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path_info = environ.get("PATH_INFO", "")

        # 1. Strip /api/index prefix if Vercel appended it during serverless invocation
        if path_info.startswith("/api/index"):
            path_info = path_info[len("/api/index"):] or "/"
            environ["PATH_INFO"] = path_info
            environ["SCRIPT_NAME"] = ""

        # 2. Check Vercel's original matched path header
        x_matched = environ.get("HTTP_X_MATCHED_PATH", "")
        if x_matched and not x_matched.startswith("/api/index"):
            environ["PATH_INFO"] = x_matched

        return self.wsgi_app(environ, start_response)


# Apply middleware wrapper to WSGI application
app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
