import datetime
from PySide6.QtCore import QThread, Signal
from git_manager.git_wrapper import GitWrapper
from database.models import HistoryRepository
from security.crypt_manager import CryptManager
from core.logger import logger

class SyncWorker(QThread):
    # Signals to communicate with the main thread
    sync_started = Signal(int) # tab_id
    sync_progress = Signal(int, str) # tab_id, log_message
    sync_finished = Signal(int, bool, str) # tab_id, success, final_message

    def __init__(self, tab_data: dict, account_data: dict, force_mode: str = "sync"):
        """
        force_mode: 'sync', 'pull', or 'push'
        """
        super().__init__()
        self.tab = tab_data
        self.account = account_data
        self.force_mode = force_mode

    def run(self):
        tab_id = self.tab["id"]
        self.sync_started.emit(tab_id)
        
        folder = self.tab["folder_path"]
        repo_name = self.tab["repo_name"]
        branch = self.tab["branch"] or "main"
        
        if not self.account:
            err = "Authentication record missing for this configuration."
            self.sync_finished.emit(tab_id, False, err)
            return

        try:
            token = CryptManager.decrypt(self.account["encrypted_token"])
        except Exception as e:
            err = f"Failed to decrypt stored credentials: {e}"
            self.sync_finished.emit(tab_id, False, err)
            return

        git = GitWrapper(folder)
        
        # 1. Initialize Git Repo
        if not git.is_repo():
            self.sync_progress.emit(tab_id, "Initializing Git repository...")
            if not git.init_repo():
                self.sync_finished.emit(tab_id, False, "Failed to initialize Git repository.")
                return
        
        git.set_user_details(self.account["username"], self.account["email"] or "synchub@noreply.github.com")
        
        # 2. Add remote URL
        remote_url = f"https://github.com/{self.account['username']}/{repo_name}.git"
        git.set_remote(remote_url)
        
        # Ensure we are on the target branch
        git.checkout_branch(branch)

        # 3. Pull Flow
        if self.force_mode in ["sync", "pull"]:
            self.sync_progress.emit(tab_id, f"Checking for updates from remote branch ({branch})...")
            pull_res = git.pull(token, remote_url, branch)
            if not pull_res["success"]:
                err_text = pull_res["stderr"] or pull_res["stdout"]
                if "Fatal: couldn't find remote ref" in err_text or "Could not resolve host" in err_text:
                    self.sync_progress.emit(tab_id, "Remote repository is empty or unreachable. Skipping pull stage.")
                else:
                    logger.warning(f"Pull warning/error: {err_text}")
                    self.sync_progress.emit(tab_id, f"Pull output: {err_text}")
            else:
                self.sync_progress.emit(tab_id, "Remote changes pulled and merged successfully.")

        if self.force_mode == "pull":
            HistoryRepository.add_log(tab_id, "Pull", "Success", message="Manual pull completed.")
            self.sync_finished.emit(tab_id, True, "Pull completed.")
            return

        # 4. Commit Local Changes
        self.sync_progress.emit(tab_id, "Scanning for local modifications...")
        git.add_all()
        status = git.get_status_summary()
        
        commit_hash = None
        if status:
            self.sync_progress.emit(tab_id, "Local changes detected. Creating commit...")
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = self.tab["commit_msg_template"].replace("{datetime}", now_str)
            
            commit_res = git.commit(commit_msg)
            if commit_res["success"]:
                commit_hash = git._run(["git", "rev-parse", "HEAD"])["stdout"][:7]
                self.sync_progress.emit(tab_id, f"Commit created locally: [{commit_hash}]")
            else:
                self.sync_finished.emit(tab_id, False, f"Local commit failed: {commit_res['stderr']}")
                return
        else:
            self.sync_progress.emit(tab_id, "No changes detected locally.")

        # 5. Push Flow
        if self.force_mode in ["sync", "push"]:
            self.sync_progress.emit(tab_id, f"Pushing branches to GitHub ({branch})...")
            push_res = git.push(token, remote_url, branch)
            if not push_res["success"]:
                err_text = push_res["stderr"] or push_res["stdout"]
                HistoryRepository.add_log(tab_id, "Push", "Failed", error_details=err_text)
                self.sync_finished.emit(tab_id, False, f"Failed to push updates: {err_text}")
                return
            else:
                self.sync_progress.emit(tab_id, "Changes successfully pushed to GitHub.")

        HistoryRepository.add_log(
            tab_id=tab_id,
            operation_type=self.force_mode.capitalize(),
            status="Success",
            commit_hash=commit_hash,
            message="Synchronization finished cleanly."
        )
        self.sync_finished.emit(tab_id, True, "Synchronization completed successfully.")