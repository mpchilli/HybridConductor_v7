import os
import subprocess
import sys

def create_directories():
    """Creates the required directory structure for the project."""
    dirs_to_create = [
        "state",
        "logs",
        "dashboard",
        "dashboard/templates",
        "data",
        "models",
        "scripts",
        "tests",
        "notebooks"
    ]
    print("Creating project directories...")
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            os.makedirs(directory)
        else:
            print(f"Directory already exists: {directory}")

def initialize_git_repo():
    """Initializes a Git repository if one does not already exist."""
    if not os.path.exists(".git"):
        print("Initializing Git repository...")
        try:
            # Use shell=True for git commands as it might be in PATH and needs shell expansion
            # check=True ensures that an error is raised if the command fails
            subprocess.run("git init", shell=True, check=True, capture_output=True, text=True)
            print("Git repository initialized successfully.")
        except FileNotFoundError:
            print("Error: Git command not found. Please ensure Git is installed and in your PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error initializing Git repository: {e.stderr}")
    else:
        print("Git repository already exists.")

def install_dependencies():
    """Installs project dependencies, including openground."""
    print("Installing dependencies (including openground)...")
    try:
        # Use sys.executable to ensure we use the pip associated with the current Python interpreter
        subprocess.run([sys.executable, "-m", "pip", "install", "openground"], check=True, capture_output=True, text=True)
        print("Dependencies installed successfully.")
    except FileNotFoundError:
        print("Error: pip command not found. Please ensure pip is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e.stderr}")

def add_binary_to_path():
    """
    Adds the user-space binary directory to the Windows PATH via the registry.
    NOTE: Modifying the registry requires administrator privileges and can be risky.
    This part is complex and platform-specific. For now, we'll print a message.
    """
    print("\nINFO: To add the user-space binary directory to your Windows PATH,")
    print("you would typically modify the system's environment variables.")
    print("This might involve editing the registry or using system settings.")
    print("This step requires manual intervention or administrator privileges.")
    print("Please refer to Windows documentation for safe procedures to update your PATH.")

def main():
    """Main function to orchestrate the setup process."""
    print("--- Hybrid Orchestrator Setup Script ---")

    # 1. Validate Python version (assuming 3.11+)
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 11):
        print("Warning: Python 3.11+ is recommended. Current version is older.")
        # Decide if this should be a hard error or a warning. For now, warning.

    create_directories()
    initialize_git_repo()
    install_dependencies()
    add_binary_to_path()

    print("\n--- Setup script finished. ---")
    print("Please review the output for any errors or warnings.")
    print("If Git was not initialized, run 'git init' manually.")
    print("If dependencies failed to install, run 'pip install openground' and others manually.")
    print("Manual intervention may be required for PATH configuration on Windows.")

if __name__ == "__main__":
    main()
