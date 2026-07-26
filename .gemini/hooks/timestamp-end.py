#!/usr/bin/env python3
"""AfterAgent hook - outputs response completion timestamp and handles host notification trigger."""
import sys
import json
import os
import time
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


def write_trigger_file():
    """Writes a trigger file to notify the host that the model finished generating its response."""
    try:
        trigger_path = "/workspace/jarvis/host-commands/.notify_trigger"
        with open(trigger_path, "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass


def main():
    try:
        raw_input = sys.stdin.read()
        json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        pass

    # Write the notification trigger file for host tracking
    write_trigger_file()

    # Return exactly the clean timestamp and tick to let Gemini CLI render it beautifully
    output = {
        "systemMessage": f" {get_time_str()} \u2713\x07"
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
