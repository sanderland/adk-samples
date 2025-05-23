import os
import platform
import shutil
from datetime import datetime

import psutil


def get_current_time():
    """Get the current date and time formatted as a string.
    
    Returns:
        str: Current datetime in format 'YYYY-MM-DD HH:MM:SS'
        
    Example:
        Agent can use this to check current time:
        > get_current_time()
        '2024-02-20 15:30:45'
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_disk_space():
    """Get disk space information for the current directory.
    
    Returns:
        str: Formatted string containing:
            - Total disk space in GB
            - Used disk space in GB  
            - Free disk space in GB
        
    Example:
        Agent can check available disk space:
        > get_disk_space()
        'Total: 500 GB
         Used: 300 GB
         Free: 200 GB'
    """
    total, used, free = shutil.disk_usage(".")
    return f"Total: {total // (2 ** 30)} GB\nUsed: {used // (2 ** 30)} GB\nFree: {free // (2 ** 30)} GB"


def get_system_info():
    """Get basic system information.
    
    Returns:
        str: Formatted string containing:
            - Operating system name and version
            - CPU information
            - Total RAM in GB
            - Available RAM in GB
            
    Example:
        Agent can check system information:
        > get_system_info()
        'OS: Windows-10-10.0.19041-SP0
         CPU: Intel64 Family 6
         Total RAM: 16 GB
         Available RAM: 8 GB'
    """
    os_info = f"{platform.system()} {platform.release()}"
    cpu_info = platform.processor()
    total_ram = round(psutil.virtual_memory().total / (2 ** 30), 2)
    available_ram = round(psutil.virtual_memory().available / (2 ** 30), 2)

    return f"OS: {os_info}\nCPU: {cpu_info}\nTotal RAM: {total_ram} GB\nAvailable RAM: {available_ram} GB"


def get_largest_files_on_disk():
    """Get the largest files on disk.

    Returns:
        str: Formatted string containing:
            - File name
            - File size in MB

    Example:
        Agent can check largest files on disk:
    """
    files = os.listdir(".")
    largest_files = sorted(files, key=lambda x: os.path.getsize(x), reverse=True)[:5]
    largest_files_str = "\n".join(
        [f"{i + 1}. {file} ({round(os.path.getsize(file) / (2 ** 20), 2)} MB)" for i, file in enumerate(largest_files)])
    return f"Largest files on disk:\n{largest_files_str}"
