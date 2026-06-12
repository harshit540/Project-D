import sys
import os
import json
import subprocess

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)

CONFIG_FILE = "config.json"


class GitSyncApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Git Repo Folder Sync")
        self.resize(700, 500)

        self.setup_ui()
        self.load_config()

        # Check if git is available on system startup
        self.check_git_availability()

    def check_git_availability(self):
        """Check if git is installed and accessible."""
        success, _ = self.run_git_command(["git", "--version"])
        if not success:
            self.log("Git is not found! Please install Git and add it to PATH.")
            # Disable buttons that rely on git
            self.connect_btn.setEnabled(False)
            self.pull_btn.setEnabled(False)
            self.push_btn.setEnabled(False)
        else:
            self.log("Git is available.")

    def setup_ui(self):
        layout = QVBoxLayout()

        # Folder Path
        folder_label = QLabel("Folder Path:")

        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select folder...")

        browse_btn = QPushButton("Browse Folder")
        browse_btn.clicked.connect(self.browse_folder)

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_btn)

        # Repo URL
        repo_label = QLabel("Repository URL:")

        self.repo_input = QLineEdit()
        self.repo_input.setPlaceholderText("https://github.com/user/repo.git")

        # Save Button
        save_btn = QPushButton("Save Config")
        save_btn.clicked.connect(self.save_config)

        # Git Buttons
        self.connect_btn = QPushButton("Connect Repo Into Folder")
        self.pull_btn = QPushButton("Pull")
        self.push_btn = QPushButton("Push")

        # Status
        status_label = QLabel("Status Log:")

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)

        layout.addWidget(folder_label)
        layout.addLayout(folder_layout)

        layout.addWidget(repo_label)
        layout.addWidget(self.repo_input)

        layout.addWidget(save_btn)
        layout.addWidget(self.connect_btn)

        git_layout = QHBoxLayout()
        git_layout.addWidget(self.pull_btn)
        git_layout.addWidget(self.push_btn)

        layout.addLayout(git_layout)

        layout.addWidget(status_label)
        layout.addWidget(self.status_box)

        self.setLayout(layout)

        # Connect buttons to methods
        self.connect_btn.clicked.connect(self.connect_repo)
        self.pull_btn.clicked.connect(self.pull_repo)
        self.push_btn.clicked.connect(self.push_repo)

    def log(self, text):
        self.status_box.append(text)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_input.setText(folder)
            self.log(f"Folder selected: {folder}")

    def save_config(self):
        data = {
            "folder": self.folder_input.text().strip(),
            "repo": self.repo_input.text().strip()
        }

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.log("Config saved successfully.")
        except Exception as e:
            self.log(f"Error saving config: {e}")

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.folder_input.setText(data.get("folder", ""))
            self.repo_input.setText(data.get("repo", ""))
            self.log("Config loaded.")
        except Exception as e:
            self.log(f"Error loading config: {e}")

    def run_git_command(self, command, cwd=None):
        """Run a git command and return (success: bool, output: str)."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def connect_repo(self):
        folder = self.folder_input.text().strip()
        repo = self.repo_input.text().strip()

        if not folder:
            self.log("Error: Select folder first.")
            return

        if not repo:
            self.log("Error: Enter repository URL.")
            return

        if not os.path.isdir(folder):
            self.log("Error: Folder does not exist.")
            return

        git_folder = os.path.join(folder, ".git")
        if os.path.exists(git_folder):
            self.log("Repository already connected.")
            return

        # Check if folder is empty
        try:
            files = os.listdir(folder)
            if len(files) != 0:
                self.log("Error: Folder must be empty for clone.")
                return
        except Exception as e:
            self.log(f"Error reading folder: {e}")
            return

        self.log("Cloning repository...")
        success, output = self.run_git_command(["git", "clone", repo, "."], cwd=folder)

        if success:
            self.log("Repository cloned successfully.")
        else:
            self.log(f"Clone Error:\n{output}")

    def pull_repo(self):
        folder = self.folder_input.text().strip()

        if not folder:
            self.log("Error: Select folder.")
            return

        self.log("Pulling...")
        success, output = self.run_git_command(["git", "pull"], cwd=folder)

        if success:
            self.log("Pull successful.")
            if output:
                self.log(output)
        else:
            self.log(f"Pull Error:\n{output}")

    def push_repo(self):
        folder = self.folder_input.text().strip()
        if not folder:
            self.log("Error: Select folder.")
            return

        # પહેલા git repository છે કે નહીં તેની ખાતરી કરો
        if not os.path.isdir(os.path.join(folder, ".git")):
            self.log("Error: Not a git repository. Connect/Clone first.")
            return

        self.log("Adding files...")
        success, output = self.run_git_command(["git", "add", "."], cwd=folder)
        if not success:
            self.log(f"Add error:\n{output}")
            return

        self.log("Creating commit...")
        success, output = self.run_git_command(
            ["git", "commit", "-m", "Auto commit from Git Sync App"],
            cwd=folder
        )

        if not success:
            # stderr અને stdout બંને ભેગા કરીને તપાસો
            combined = (output + " " + self.run_git_command(["git", "commit", "-m", "test"], cwd=folder)[1]).lower()
            if "nothing to commit" in combined or "nothing added to commit" in combined:
                self.log("Nothing to commit. Push skipped.")
                return
            elif "please tell me who you are" in combined or "identity" in combined:
                self.log("Git user.name/user.email not set. Run:\n"
                        "  git config --global user.name 'Your Name'\n"
                        "  git config --global user.email 'your@email.com'")
                return
            else:
                self.log(f"Commit error:\n{output}")
                # સંપૂર્ણ ડિબગ માટે stdout પણ બતાવો
                success2, out2 = self.run_git_command(["git", "commit", "-m", "Auto commit"], cwd=folder)
                if out2:
                    self.log(f"Additional info:\n{out2}")
                return

        # Commit સફળ થયો હોય તો જ push કરો
        self.log("Pushing...")
        success, output = self.run_git_command(["git", "push"], cwd=folder)

        if success:
            self.log("Push successful.")
            if output:
                self.log(output)
        else:
            self.log(f"Push Error:\n{output}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GitSyncApp()
    window.show()
    sys.exit(app.exec())