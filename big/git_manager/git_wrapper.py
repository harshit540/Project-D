import os
import subprocess
from core.logger import logger

class GitWrapper:
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

    def _run(self, args: list, token: str = None) -> dict:
        env = os.environ.copy()
        if token:
            # Suppress terminal authentication popups
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = ""

        try:
            # Use startupinfo to keep console windows hidden on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            result = subprocess.run(
                args,
                cwd=self.workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=env,
                startupinfo=startupinfo,
                timeout=45
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "code": result.returncode
            }
        except Exception as e:
            logger.error(f"Executing git system call failed {args}: {e}")
            return {"success": False, "stdout": "", "stderr": str(e), "code": -1}

    def is_repo(self) -> bool:
        if not os.path.exists(os.path.join(self.workspace_path, ".git")):
            return False
        res = self._run(["git", "rev-parse", "--is-inside-work-tree"])
        return res["success"]

    def init_repo(self) -> bool:
        os.makedirs(self.workspace_path, exist_ok=True)
        return self._run(["git", "init"])["success"]

    def set_user_details(self, name: str, email: str):
        self._run(["git", "config", "user.name", name])
        self._run(["git", "config", "user.email", email])

    def has_remote(self) -> bool:
        res = self._run(["git", "remote"])
        return len(res["stdout"]) > 0

    def set_remote(self, url: str):
        self._run(["git", "remote", "remove", "origin"])
        return self._run(["git", "remote", "add", "origin", url])["success"]

    def add_all(self):
        return self._run(["git", "add", "."])

    def commit(self, message: str) -> dict:
        return self._run(["git", "commit", "-m", message])

    def get_current_branch(self) -> str:
        res = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return res["stdout"] if res["success"] else "main"

    def checkout_branch(self, branch: str) -> bool:
        res = self._run(["git", "checkout", branch])
        if not res["success"]:
            # Create local branch if it doesn't exist
            res = self._run(["git", "checkout", "-b", branch])
        return res["success"]

    def fetch(self, token: str, remote_url: str) -> dict:
        authed_url = remote_url.replace("https://", f"https://x-access-token:{token}@")
        return self._run(["git", "fetch", authed_url], token=token)

    def pull(self, token: str, remote_url: str, branch: str) -> dict:
        authed_url = remote_url.replace("https://", f"https://x-access-token:{token}@")
        return self._run(["git", "pull", authed_url, branch], token=token)

    def push(self, token: str, remote_url: str, branch: str) -> dict:
        authed_url = remote_url.replace("https://", f"https://x-access-token:{token}@")
        return self._run(["git", "push", "-u", authed_url, f"HEAD:{branch}"], token=token)

    def get_diff(self) -> str:
        res = self._run(["git", "diff", "HEAD"])
        return res["stdout"] if res["success"] else ""

    def get_status_summary(self) -> str:
        res = self._run(["git", "status", "--short"])
        return res["stdout"] if res["success"] else ""