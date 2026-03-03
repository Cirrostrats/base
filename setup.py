from pathlib import Path
import argparse
import os
import shutil
import sys
import subprocess

# repositories
frontend_repo = "https://github.com/ujazishere/cirrostrats-frontend.git"
backend_repo = "https://github.com/ujazishere/cirrostrats-backend.git"


def get_editor_choice():
    """Ask user to choose nano or vim for editing .env files."""
    while True:
        choice = input("Use nano or vim for editing .env files? (nano/vim) [nano]: ").strip().lower() or "nano"
        if choice in ("nano", "n"):
            return "nano"
        if choice in ("vim", "v"):
            return "vim"
        print("  Please enter 'nano' or 'vim'.")


def get_branch_from_user():
    """Ask user which branch to use; default to dev if not specified."""
    branch = input("Which branch do you want to use? (default: dev): ").strip()
    return branch if branch else "dev"


def branch_work(repo_link: str, folder: str, branch: str) -> None:
    """Clone repo (if needed) and checkout the given branch, tracking remote."""

    folder_path = os.path.join(os.getcwd(), folder)
    print("Currently attempting to work in folder_path path:", folder_path)

    folder_path_exists = os.path.exists(folder_path)
    base_path = os.getcwd()

    if not folder_path_exists:
        print(f"Cloning {folder} repo on this machine...")
        subprocess.run(["git", "clone", repo_link, folder], check=True)
        os.chdir(folder_path)
        subprocess.run(["git", "fetch", "origin"], check=True)
        # Track remote branch: creates local branch tracking origin/<branch>
        track = subprocess.run(
            ["git", "checkout", "-t", f"origin/{branch}"],
            capture_output=True,
            text=True,
        )
        if track.returncode != 0 and "already exists" in (track.stderr or ""):
            subprocess.run(["git", "checkout", branch], check=True)
            subprocess.run(["git", "pull", "origin", branch], check=True)
    else:
        print(f"{folder} repo already exists on this machine")
        print("Current working directory:", os.getcwd())
        os.chdir(folder_path)
        print("Updated cwd:", os.getcwd())
        subprocess.run(["git", "fetch", "origin"], check=True)
        track = subprocess.run(
            ["git", "checkout", "-t", f"origin/{branch}"],
            capture_output=True,
            text=True,
        )
        if track.returncode != 0:
            if "already exists" in (track.stderr or ""):
                subprocess.run(["git", "checkout", branch], check=True)
                subprocess.run(["git", "pull", "origin", branch], check=True)
            else:
                print(track.stderr or track.stdout or "Checkout failed.")
                sys.exit(1)

    os.chdir(base_path)
    print("Finally updated cwd to:", os.getcwd())


def setup_env_file(project_dir: str, project_name: str, editor: str) -> None:
    """
    Create .env from .env.example if needed, then open it in the user's editor.
    project_dir is the path to the repo (e.g. cirrostrats-frontend).
    editor is 'nano' or 'vim'.
    """
    base = Path(os.getcwd())
    dir_path = base / project_dir
    example = dir_path / ".env.example"
    env_file = dir_path / ".env"

    if not dir_path.is_dir():
        print(f"  Skipping {project_name} .env setup: directory {project_dir} not found.")
        return

    if example.exists():
        if not env_file.exists():
            shutil.copy2(example, env_file)
            print(f"  Created {env_file} from .env.example")
        else:
            print(f"  {env_file} already exists (not overwriting).")
    else:
        if not env_file.exists():
            env_file.touch()
            print(f"  Created empty {env_file} (no .env.example in {project_dir}).")

    input(f"  Press Enter to open {project_name} .env in your editor for editing...")
    try:
        subprocess.run([editor, str(env_file)], check=True)
    except FileNotFoundError:
        print(f"  Editor '{editor}' not found. Edit manually: {env_file}")
    except subprocess.CalledProcessError:
        print(f"  Editor exited with an error. Edit manually if needed: {env_file}")
    input(f"  Press Enter when done editing {project_name} .env to continue...")
    print()


def configure_journald_limits(editor: str) -> None:
    """
    Cap systemd-journald storage so /var/log/journal never grows unbounded.
    Prompts the user to review the defaults, optionally edit them, then apply.

    Requires root / sudo; skipped silently if not running as root so the rest
    of setup can still proceed on a development machine.
    """
    if os.geteuid() != 0:
        print("  [journald] Skipping journal limit config — not running as root.")
        return

    conf_dir = Path("/etc/systemd/journald.conf.d")
    conf_file = conf_dir / "99-size-limit.conf"

    conf_dir.mkdir(parents=True, exist_ok=True)

    default_conf = (
        "# Managed by setup.py — limits /var/log/journal growth for long-term stability.\n"
        "[Journal]\n"
        "SystemMaxUse=200M\n"
        "SystemMaxFileSize=50M\n"
        "MaxRetentionSec=2weeks\n"
    )

    customize = input(
        "  [journald] Using defaults (SystemMaxUse=200M, SystemMaxFileSize=50M, MaxRetentionSec=2weeks)."
        " Want to specify something else? (yes) [no]: "
    ).strip().lower()

    if customize in ("yes", "y"):
        conf_file.write_text(default_conf)
        print(f"  [journald] Opening {conf_file} in {editor} for editing...")
        try:
            subprocess.run([editor, str(conf_file)], check=True)
        except FileNotFoundError:
            print(f"  Editor '{editor}' not found. Edit manually: {conf_file}")
        except subprocess.CalledProcessError:
            print(f"  Editor exited with an error. Using file as-is: {conf_file}")
    else:
        conf_file.write_text(default_conf)
        print(f"  [journald] Wrote default config to {conf_file}.")

    result = subprocess.run(
        ["systemctl", "restart", "systemd-journald"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  [journald] systemd-journald restarted — limits are now active.")
    else:
        print(f"  [journald] Warning: could not restart systemd-journald: {result.stderr.strip()}")

    vacuum = subprocess.run(
        ["journalctl", "--vacuum-size=200M", "--vacuum-time=2weeks"],
        capture_output=True, text=True,
    )
    if vacuum.returncode == 0:
        print(f"  [journald] Vacuum complete. {vacuum.stdout.strip()}")
    else:
        print(f"  [journald] Vacuum warning: {vacuum.stderr.strip()}")


def main():
    parser = argparse.ArgumentParser(description="Setup Cirrostrats frontend and backend repos.")
    parser.add_argument(
        "-b", "--branch",
        type=str,
        default=None,
        help="Branch to clone/checkout (e.g. dev, main). If omitted, you will be prompted; default is dev.",
    )
    args = parser.parse_args()

    branch = args.branch
    if branch is None:
        branch = get_branch_from_user()
    print(f"Using branch: {branch}")

    branch_work(repo_link=frontend_repo, folder="cirrostrats-frontend", branch=branch)
    branch_work(repo_link=backend_repo, folder="cirrostrats-backend", branch=branch)

    print("*** .env setup: .env files will be created from .env.example (if present) and opened for editing.\n")
    editor = get_editor_choice()
    print(f"  Using {editor} for editing.\n")
    setup_env_file("cirrostrats-frontend", "frontend", editor)
    setup_env_file("cirrostrats-backend", "backend", editor)

    print("\n*** Configuring systemd-journald rolling log limits...")
    configure_journald_limits(editor)

    print("\nCheck compose markdown file, verify appropriate env files are in entirity and spin according to needs - dev, prod or homelab is available.")
    # subprocess.run(["docker", "compose", "up"])


if __name__ == "__main__":
    main()
