import urllib.request
import urllib.parse
import json
from core.logger import logger

class GitHubClient:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"token {self.token}",
            "User-Agent": "SyncHub-App",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_repositories(self):
        url = "https://api.github.com/user/repos?per_page=100&type=owner"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                return json.loads(res.read().decode())
        except Exception as e:
            logger.error(f"Could not load GitHub repos: {e}")
            raise e

    def create_repository(self, name, description, is_private, init_readme, license_template):
        url = "https://api.github.com/user/repos"
        payload = {
            "name": name,
            "description": description,
            "private": is_private,
            "auto_init": init_readme
        }
        if license_template and license_template != "None":
            payload["license_template"] = license_template

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                return json.loads(res.read().decode())
        except Exception as e:
            logger.error(f"Failed to create remote repository: {e}")
            raise e