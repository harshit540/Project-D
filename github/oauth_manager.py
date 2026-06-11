import os
import threading
import urllib.request
import urllib.parse
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from PySide6.QtCore import QObject, Signal
from core.logger import logger

# Developer-provided client application defaults
DEFAULT_CLIENT_ID = "Ov23lidXHd3dXYQEpJ22" 
DEFAULT_CLIENT_SECRET = "51a842b83c9dd9b0bee67c3ac23931c1736c7ab3" # Set via GitHub settings or UI

class OAuthSignals(QObject):
    auth_finished = Signal(dict)
    auth_failed = Signal(str)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Prevent terminal console pollution
        pass

    def do_GET(self):
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code = query_components.get("code")

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        if code:
            code_str = code[0]
            self.server.oauth_manager.exchange_code_for_token(code_str)
            html = """
            <html>
                <body style="font-family: sans-serif; text-align: center; padding-top: 50px; background-color: #1e1e2e; color: #cdd6f4;">
                    <h2 style="color: #a6e3a1;">Authentication Successful!</h2>
                    <p>SyncHub has registered your token. You may close this browser tab safely.</p>
                </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.server.oauth_manager.signals.auth_failed.emit("No validation code found.")
            self.wfile.write(b"Authorization failed.")

class OAuthManager:
    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id or DEFAULT_CLIENT_ID
        self.client_secret = client_secret or DEFAULT_CLIENT_SECRET
        self.port = 52412
        self.signals = OAuthSignals()
        self.server = None
        self.server_thread = None

    def start_local_server(self):
        def run_server():
            self.server = HTTPServer(("localhost", self.port), OAuthCallbackHandler)
            self.server.oauth_manager = self
            self.server.handle_request() # Listen exactly once

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"OAuth Loopback Receiver listening on port {self.port}.")

    def get_auth_url(self) -> str:
        self.start_local_server()
        scopes = "repo read:user user:email"
        params = {
            "client_id": self.client_id,
            "redirect_uri": f"http://localhost:{self.port}/callback",
            "scope": scopes,
            "response_type": "code"
        }
        return "https://github.com/login/oauth/authorize?" + urllib.parse.urlencode(params)

    def exchange_code_for_token(self, code):
        def _exchange():
            url = "https://github.com/login/oauth/access_token"
            data = urllib.parse.urlencode({
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code
            }).encode("utf-8")

            req = urllib.request.Request(url, data=data, headers={"Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode())
                    access_token = res_data.get("access_token")
                    if access_token:
                        self.fetch_user_details(access_token)
                    else:
                        error_msg = res_data.get("error_description", "Invalid response fields.")
                        self.signals.auth_failed.emit(error_msg)
            except Exception as e:
                logger.error(f"Token exchange exception: {e}")
                self.signals.auth_failed.emit(str(e))

        threading.Thread(target=_exchange, daemon=True).start()

    def fetch_user_details(self, token):
        try:
            # Fetch User Profile
            req = urllib.request.Request(
                "https://api.github.com/user",
                headers={"Authorization": f"token {token}", "User-Agent": "SyncHub-App"}
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                profile = json.loads(res.read().decode())
                username = profile.get("login")
                avatar_url = profile.get("avatar_url")

            # Fetch User Email
            email = "no-reply@github.com"
            req_email = urllib.request.Request(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {token}", "User-Agent": "SyncHub-App"}
            )
            with urllib.request.urlopen(req_email, timeout=10) as res_email:
                emails = json.loads(res_email.read().decode())
                for item in emails:
                    if item.get("primary") and item.get("verified"):
                        email = item.get("email")
                        break

            self.signals.auth_finished.emit({
                "username": username,
                "email": email,
                "token": token,
                "avatar_url": avatar_url
            })
        except Exception as e:
            logger.error(f"Error fetching GitHub profile: {e}")
            self.signals.auth_failed.emit(f"Could not fetch user details: {e}")