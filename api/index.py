import os
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure VERCEL environment flag is active
os.environ["VERCEL"] = "1"

import server

# Ensure database is initialized in /tmp
server.init_db()


class handler(server.AgoraHandler):
    def get_effective_path(self):
        # Resolve path from Vercel rewrite headers if available
        raw_path = (
            self.headers.get("x-forwarded-uri")
            or self.headers.get("x-matched-path")
            or self.headers.get("x-invoke-path")
            or self.path
        )
        return raw_path.split("?")[0]

    def do_GET(self):
        if not hasattr(self, "requestline"):
            self.requestline = f"GET {self.path} HTTP/1.1"
        if not hasattr(self, "request_version"):
            self.request_version = "HTTP/1.1"
        eff_path = self.get_effective_path()
        original_path = self.path
        self.path = eff_path
        try:
            super().do_GET()
        finally:
            self.path = original_path

    def do_POST(self):
        if not hasattr(self, "requestline"):
            self.requestline = f"POST {self.path} HTTP/1.1"
        if not hasattr(self, "request_version"):
            self.request_version = "HTTP/1.1"
        eff_path = self.get_effective_path()
        original_path = self.path
        self.path = eff_path
        try:
            super().do_POST()
        finally:
            self.path = original_path
