import shutil
from datetime import datetime


def get_current_time():
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_disk_space():
    """Get disk space information including total, used and free memory in GB."""
    total, used, free = shutil.disk_usage(".")
    return f"Total: {total // (2 ** 30)} GB\nUsed: {used // (2 ** 30)} GB\nFree: {free // (2 ** 30)} GB"
