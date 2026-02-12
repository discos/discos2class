import os
import subprocess

def check_drive_status(path, ip):

    mounted = (
        os.path.exists(path) and
        os.path.isdir(path) and
        os.access(path, os.R_OK)
    )   

    is_mount = os.path.ismount(path)

    reachable = False
    if ip:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        reachable = result.returncode == 0

    return {
        "mounted": mounted,
        "is_mount": is_mount,
        "reachable": reachable,
        "path": path,
        "ip": ip
    }
