import json
import os
import sys
import urllib.parse
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
        # 1. Check rewrite query parameter ?__path=... or ?path=...
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if "__path" in qs:
            sub = qs["__path"][0].strip("/")
            return f"/api/{sub}"
        if "path" in qs:
            sub = qs["path"][0].strip("/")
            return f"/api/{sub}"

        # 2. Check Vercel headers if present
        for h in ["x-vercel-matched-path", "x-matched-path", "x-forwarded-uri", "x-invoke-path"]:
            v = self.headers.get(h)
            if v and "/api/" in v:
                return v.split("?")[0]

        # 3. If path is already /api/... and not index.py
        if parsed.path.startswith("/api/") and not parsed.path.endswith("index.py") and not parsed.path.endswith("index"):
            return parsed.path

        return parsed.path

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
