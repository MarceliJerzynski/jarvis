#!/usr/bin/env python3
"""BeforeAgent hook - outputs prompt submission timestamp and cleans up the host notification trigger."""
import sys
import json
import os
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


def get_time_str():
    if ZoneInfo is not None:
        try:
            now_dt = datetime.now(ZoneInfo("Europe/Warsaw"))
        except Exception:
            now_dt = datetime.now()
    else:
        now_dt = datetime.now()
    return now_dt.strftime("%H:%M:%S")


def clean_host_commands_dir():
    """Cleans up all files in the host-commands directory at the start of a new generation to remove stale files."""
    try:
        dir_path = "/workspace/jarvis/host-commands"
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    except Exception:
        pass


def write_cancel_file():
    """Writes a cancel file to signal the host daemon to abort any pending notification wait loops."""
    try:
        cancel_path = "/workspace/jarvis/host-commands/.notify_cancel"
        with open(cancel_path, "w") as f:
            f.write("cancel")
    except Exception:
        pass


def main():
    try:
        raw_input = sys.stdin.read()
        json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        pass

    # Clean up all stale host commands first, then signal cancellation of pending notifications
    clean_host_commands_dir()
    write_cancel_file()

    output = {
        "systemMessage": f" {get_time_str()} \u2192"
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
