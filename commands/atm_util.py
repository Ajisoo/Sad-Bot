from globals import CONTENT_FOLDER
import os


async def cmd_status():
    path = os.path.join(CONTENT_FOLDER, "atmstatus.txt")

    try:
        with open(path, "r") as f:
            status = f.read().strip().upper()

        return True if status == "RELEASE" else False if status == "BETA" else None

    except FileNotFoundError:
        return None