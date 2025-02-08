#!/usr/bin/env python3
import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional


class DevEnvironmentManager:
    """Class to manage development environment setup

    Attributes:
        home: Home directory path
        dotfiles_path: Path to dotfiles directory
        is_windows: True if running on Windows
        is_macos: True if running on macOS
        logger: Logger instance
    """

    def __init__(self, dotfiles_path: Optional[str] = None):
        self.home = str(Path.home())
        self.dotfiles_path = dotfiles_path or os.path.join(self.home, "dotfiles")
        self.is_windows = platform.system() == "Windows"
        self.is_macos = platform.system() == "Darwin"

        # Setup logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def run_command(self, command: list[str]) -> bool:
        """Run a shell command and handle errors"""
        try:
            subprocess.run(command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(command)}")
            self.logger.error(f"Error: {str(e)}")
            return False

    def backup_existing_config(self, config_path: str) -> None:
        """Backup existing configuration file if it exists"""
        if os.path.exists(config_path):
            backup_path = f"{config_path}.backup"
            shutil.move(config_path, backup_path)
            self.logger.info(f"Backed up existing config: {backup_path}")

    def create_symlink(self, source: str, target: str) -> None:
        """Create a symlink, handling both Windows and Unix systems"""
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(target), exist_ok=True)

            # Remove existing symlink or file
            if os.path.exists(target):
                if os.path.islink(target):
                    os.unlink(target)
                else:
                    self.backup_existing_config(target)

            # Create the symlink
            if self.is_windows:
                if os.path.isdir(source):
                    os.system(f'mklink /D "{target}" "{source}"')
                else:
                    os.system(f'mklink "{target}" "{source}"')
            else:
                os.symlink(source, target)

            self.logger.info(f"Created symlink: {target} -> {source}")
        except Exception as e:
            self.logger.error(f"Failed to create symlink: {str(e)}")

    def install_packages(self) -> None:
        """Install necessary packages based on OS"""
        self.logger.info("Installing necessary packages...")

        if self.is_macos:
            # Check if Homebrew is installed
            if not shutil.which("brew"):
                self.logger.info("Installing Homebrew...")
                brew_install = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                os.system(brew_install)

            # Install packages
            packages = ["python3", "git", "visual-studio-code", "iterm2", "zsh"]
            for package in packages:
                self.run_command(["brew", "install", package])

        elif self.is_windows:
            self.logger.info("Please ensure you have the following installed:")
            self.logger.info("1. Python (from python.org)")
            self.logger.info("2. Git (from git-scm.com)")
            self.logger.info("3. VS Code (from code.visualstudio.com)")
            input("Press Enter when ready to continue...")

    def setup_vscode(self) -> None:
        """Setup VS Code configuration and extensions"""
        self.logger.info("Setting up VS Code...")

        # Determine VS Code config path
        if self.is_windows:
            vscode_config_path = os.path.join(
                self.home, "AppData", "Roaming", "Code", "User"
            )
        else:
            vscode_config_path = os.path.join(
                self.home, "Library", "Application Support", "Code", "User"
            )

        # Create symlinks for VS Code settings
        settings_source = os.path.join(self.dotfiles_path, "vscode", "settings.json")
        keybindings_source = os.path.join(
            self.dotfiles_path, "vscode", "keybindings.json"
        )
        snippets_source = os.path.join(self.dotfiles_path, "vscode", "snippets")

        self.create_symlink(
            settings_source, os.path.join(vscode_config_path, "settings.json")
        )
        self.create_symlink(
            keybindings_source, os.path.join(vscode_config_path, "keybindings.json")
        )
        self.create_symlink(
            snippets_source, os.path.join(vscode_config_path, "snippets")
        )

        # Install extensions
        extensions_file = os.path.join(self.dotfiles_path, "vscode", "extensions.txt")
        if os.path.exists(extensions_file):
            with open(extensions_file) as f:
                for ext in f:
                    ext = ext.strip()
                    if ext:
                        self.run_command(["code", "--install-extension", ext])

    def setup_python_env(self) -> None:
        """Setup Python environment and packages"""
        self.logger.info("Setting up Python environment...")

        requirements_file = os.path.join(
            self.dotfiles_path, "python", "requirements.txt"
        )
        if os.path.exists(requirements_file):
            self.run_command(["pip", "install", "-r", requirements_file])

        # Create and configure virtual environment if needed
        venv_path = os.path.join(self.dotfiles_path, "python", "venv")
        if not os.path.exists(venv_path):
            self.run_command(["python", "-m", "venv", venv_path])

    def setup_git(self) -> None:
        """Setup Git configuration"""
        self.logger.info("Setting up Git configuration...")

        gitconfig_source = os.path.join(self.dotfiles_path, "git", ".gitconfig")
        gitconfig_target = os.path.join(self.home, ".gitconfig")
        self.create_symlink(gitconfig_source, gitconfig_target)

    def setup_zsh(self) -> None:
        """Setup Zsh and Oh My Zsh configuration"""
        if not self.is_windows:
            self.logger.info("Setting up Zsh configuration...")

            # Install Oh My Zsh if not already installed
            omz_path = os.path.join(self.home, ".oh-my-zsh")
            if not os.path.exists(omz_path):
                omz_install = 'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'
                os.system(omz_install)

            # Setup Zsh configuration
            zshrc_source = os.path.join(self.dotfiles_path, "zsh", ".zshrc")
            zshrc_target = os.path.join(self.home, ".zshrc")
            self.create_symlink(zshrc_source, zshrc_target)

    def setup_iterm(self) -> None:
        """Setup iTerm2 configuration"""
        if self.is_macos:
            self.logger.info("Setting up iTerm2 configuration...")

            iterm_source = os.path.join(
                self.dotfiles_path, "iterm2", "com.googlecode.iterm2.plist"
            )
            iterm_target = os.path.join(
                self.home, "Library", "Preferences", "com.googlecode.iterm2.plist"
            )
            self.create_symlink(iterm_source, iterm_target)

            # Load custom preferences
            os.system(
                f"defaults write com.googlecode.iterm2 LoadPrefsFromCustomFolder -bool true"
            )
            os.system(
                f"defaults write com.googlecode.iterm2 PrefsCustomFolder -string {os.path.dirname(iterm_source)}"
            )

    def setup_all(self) -> None:
        """Run complete setup process"""
        self.logger.info("Starting development environment setup...")

        # Create dotfiles directory if it doesn't exist
        os.makedirs(self.dotfiles_path, exist_ok=True)

        # Run setup steps
        # self.install_packages()
        self.setup_git()
        self.setup_vscode()
        # self.setup_python_env()

        # if not self.is_windows:
        #     self.setup_zsh()
        #     self.setup_iterm()

        self.logger.info("Setup complete! 🎉")

        if self.is_windows:
            self.logger.info("\nNote: Some features are not available on Windows.")
            self.logger.info("Consider using WSL2 for a more Unix-like experience.")


def main():
    """Main entry point for script
    Reads the dotfiles path from the environment variable DOTFILES_PATH
    or uses the default path ~/dotfiles

    Creates a DevEnvironmentManager instance and runs the setup process
    """
    # Get dotfiles path from environment variable or use default
    dotfiles_path = os.getenv("DOTFILES_PATH") or os.path.join(
        str(Path.home()), "dotfiles"
    )

    # Initialize and run setup
    manager = DevEnvironmentManager(dotfiles_path)
    manager.setup_all()


if __name__ == "__main__":
    main()
