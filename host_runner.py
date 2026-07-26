#!/usr/bin/env python3
"""
Host Runner Daemon
This script runs on your host machine (not in the container).
It listens to global keyboard and mouse events to track user idle time,
and watches for the .notify_trigger file written inside the host-commands directory by the AfterAgent container hook.
When a trigger is detected, it waits until you have been idle for 10 seconds,
then plays the look-here-marceli.mp3 file in the background.

Dependencies on Host:
    pip install pynput

Usage:
    python host_runner.py
"""

import os
import sys
import time
import subprocess

try:
    from pynput import mouse, keyboard
except ImportError:
    print("Error: 'pynput' library is not installed on your host.")
    print("Please run: pip install pynput")
    sys.exit(1)

# Paths relative to the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRIGGER_PATH = os.path.join(SCRIPT_DIR, "host-commands", ".notify_trigger")
CANCEL_PATH = os.path.join(SCRIPT_DIR, "host-commands", ".notify_cancel")
MP3_PATH = os.path.join(SCRIPT_DIR, "utils", "look-here-marceli.mp3")

# Shared state for tracking activity
last_activity_time = time.time()
last_logged_time = 0.0


def update_activity(*args, **kwargs):
    """Updates the last user activity timestamp and logs it with a throttle to avoid terminal flooding."""
    global last_activity_time, last_logged_time
    current_time = time.time()
    last_activity_time = current_time

    # Throttle activity logs to at most once every 2 seconds to keep console clean
    if current_time - last_logged_time >= 2.0:
        print(f"[{time.strftime('%H:%M:%S')}] Active: Host input detected (mouse/keyboard).")
        last_logged_time = current_time


def play_audio(file_path):
    """Attempts to play the audio file using common host utilities."""
    if not os.path.exists(file_path):
        print(f"Warning: Audio file not found at {file_path}")
        # Standard fallback terminal beep
        sys.stdout.write("\a")
        sys.stdout.flush()
        return

    print(f"Playing notification sound: {file_path}")

    # Platform-specific background player detection
    if sys.platform == "darwin":  # macOS
        print("Running afplay on macOS...")
        subprocess.Popen(["afplay", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == "win32":  # Windows
        # Use PowerShell with the correct PresentationCore and System.Windows.Media.MediaPlayer namespace
        win_path = os.path.abspath(file_path).replace('/', '\\')
        print(f"Running PowerShell MediaPlayer on Windows for: {win_path}")
        ps_command = (
            f"Add-Type -AssemblyName PresentationCore; "
            f"$player = New-Object System.Windows.Media.MediaPlayer; "
            f"$player.Open('{win_path}'); "
            f"$player.Play(); "
            f"Start-Sleep -s 10"
        )
        subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command", ps_command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:  # Linux / Unix
        # Try to find an available CLI player with native MP3 support
        players = [
            ["mpg123", "-q"],           # Popular CLI MP3 player
            ["ffplay", "-nodisp", "-autoexit"], # FFmpeg
            ["mplayer", "-really-quiet"],
            ["cvlc", "--play-and-exit"], # VLC CLI
            ["pw-play"],                # PipeWire (usually WAV only)
            ["paplay"],                 # PulseAudio (usually WAV only)
        ]

        for player_cmd in players:
            try:
                cmd = player_cmd[0]
                subprocess.run(["which", cmd], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"Executing player: {' '.join(player_cmd)} {file_path}")
                full_cmd = player_cmd + [file_path]
                subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        # If no player found, fallback to PC speaker beep
        print("Warning: No background audio player found on the host (please install mpg123, ffplay, or mplayer). Using PC beep.")
        sys.stdout.write("\a")
        sys.stdout.flush()


def main():
    global last_activity_time
    print("─────────────────────────────────────────────────────────────────")
    print("Host Runner Daemon has started successfully!")
    print(f"Watching for trigger at: {TRIGGER_PATH}")
    print(f"Audio file location:      {MP3_PATH}")
    print("Monitoring mouse and keyboard activity on host...")
    print("─────────────────────────────────────────────────────────────────")

    # Start global input listeners on host system
    mouse_listener = mouse.Listener(
        on_move=update_activity,
        on_click=update_activity,
        on_scroll=update_activity
    )
    keyboard_listener = keyboard.Listener(
        on_press=update_activity
    )

    mouse_listener.start()
    keyboard_listener.start()

    # Reset trigger file and cancel file on startup if they exist
    for path in (TRIGGER_PATH, CANCEL_PATH):
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    try:
        while True:
            if os.path.exists(TRIGGER_PATH):
                # Notification trigger found, record the trigger timestamp and remove the file
                trigger_time = time.time()
                try:
                    os.remove(TRIGGER_PATH)
                except Exception:
                    pass

                # Clear any existing cancel file from the current prompt's start before starting the wait loop
                if os.path.exists(CANCEL_PATH):
                    try:
                        os.remove(CANCEL_PATH)
                    except Exception:
                        pass

                print("AI response finished. Waiting for user to become idle...")

                # Loop and check if user has been inactive for at least 10 seconds relative to both last activity and trigger completion
                while True:
                    # If a cancel file is found, user started a new prompt, so abort waiting
                    if os.path.exists(CANCEL_PATH):
                        try:
                            os.remove(CANCEL_PATH)
                        except Exception:
                            pass
                        print("New prompt started by user. Aborting pending notification loop.")
                        break

                    current_time = time.time()
                    # If user was idle during generation, start counting the 10s exactly from when the AI finished generating
                    effective_activity_time = max(last_activity_time, trigger_time)
                    idle_duration = current_time - effective_activity_time
                    if idle_duration >= 10.0:
                        play_audio(MP3_PATH)
                        break
                    time.sleep(0.5)

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping host daemon. Goodbye!")
        mouse_listener.stop()
        keyboard_listener.stop()


if __name__ == "__main__":
    main()
