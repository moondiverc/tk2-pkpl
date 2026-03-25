import base64
import json
import urllib.parse
import webbrowser
import http.server
import socketserver
import threading
import requests
import secrets


class SimpleOAuth2Client:
    def __init__(self, client_id, client_secret, auth_url, token_url, redirect_uri, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.code = None
        self.token = None

    def get_authorization_code(self):
        state = secrets.token_urlsafe(16)

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'response_type': 'code',
            'state': state
        }

        auth_request_url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"

        oauth_client = self

        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Authentication successful! You can close this window.")

                query = urllib.parse.urlparse(self.path).query
                query_params = urllib.parse.parse_qs(query)

                if 'code' in query_params:
                    oauth_client.code = query_params['code'][0]

                threading.Thread(target=server.shutdown).start()

            def log_message(self, format, *args):
                return

        port = int(urllib.parse.urlparse(self.redirect_uri).port or 8000)

        server = socketserver.TCPServer(("", port), CallbackHandler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        print(f"Opening browser to authorize: {auth_request_url}")
        webbrowser.open(auth_request_url)

        server_thread.join()

        if not self.code:
            raise Exception("Failed to get authorization code")

        return self.code

    def get_token(self, code=None):
        if code:
            self.code = code

        if not self.code:
            self.get_authorization_code()

        data = {
            'grant_type': 'authorization_code',
            'code': self.code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.token_url, data=data)

        if response.status_code != 200:
            raise Exception(f"Failed to get token: {response.text}")

        self.token = response.json()
        return self.token

    def refresh_token(self):
        if not self.token or 'refresh_token' not in self.token:
            raise Exception("No refresh token available")

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.token['refresh_token'],
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.token_url, data=data)

        if response.status_code != 200:
            raise Exception(f"Failed to refresh token: {response.text}")

        self.token.update(response.json())
        return self.token

    def make_api_request(self, url, method='GET', headers=None, data=None):
        if not self.token:
            raise Exception("No access token available")

        if headers is None:
            headers = {}
        headers['Authorization'] = f"Bearer {self.token['access_token']}"

        response = requests.request(method, url, headers=headers, json=data)
        return response


if __name__ == "__main__":
    # Example configuration for Google OAuth
    client = SimpleOAuth2Client(
        client_id="....",
        client_secret="....",
        auth_url="https://accounts.google.com/o/oauth2/auth",
        token_url="https://oauth2.googleapis.com/token",
        redirect_uri="http://localhost:8000/callback",
        scope="profile email"
    )

    # Get token
    token = client.get_token()
    print("Access token:", token['access_token'])

    # Make an API request (example for Google)
    response = client.make_api_request("https://www.googleapis.com/oauth2/v2/userinfo")
    print("User info:", response.json())