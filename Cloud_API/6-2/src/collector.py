import subprocess


def get_git_status() -> str:
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True
    )
    return result.stdout


def get_git_diff() -> str:
    result = subprocess.run(
        ["git", "diff"],
        capture_output=True, text=True
    )
    return result.stdout


def get_current_branch() -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True
    )
    return result.stdout.strip()
