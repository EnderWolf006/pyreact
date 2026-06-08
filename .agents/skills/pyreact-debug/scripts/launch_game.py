# -*- coding: utf-8 -*-
"""
Launch Minecraft.Windows.exe and start a detached log server.

Usage:
    python launch_game.py [--config FILE] [--project DIR] [--port PORT] [--log-output FILE]
"""

import argparse
import os
import subprocess
import socket
import sys
import time

from _mcs import get_minecraft_exe, find_latest_cppconfig, setup_runtime

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", "..", "..", ".."))

_READY_SIGNAL = '=====> PyreactRuntime AppReady:'


def _find_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _poll_ready(port, deadline):
    """Poll log_server HTTP API until AppReady signal appears or deadline."""
    try:
        from urllib.request import urlopen
        from urllib.parse import urlencode
    except ImportError:
        from urllib2 import urlopen
        from urllib import urlencode
    import json

    seen = 0
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            url = "http://localhost:%d/logs?since=%d&grep=%s" % (
                port + 1, seen, "PyreactRuntime+AppReady"
            )
            resp = urlopen(url, timeout=3)
            data = json.loads(resp.read().decode('utf-8'))
            seen = data["total"]
            for entry in data["lines"]:
                if _READY_SIGNAL in entry["text"]:
                    return True
        except Exception:
            pass
    return False


def main():
    parser = argparse.ArgumentParser(description="Launch Minecraft game + detached log server")
    parser.add_argument("--config", default=None)
    parser.add_argument("--project", default=None)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--log-output", default=None)
    args = parser.parse_args()

    exe = get_minecraft_exe()
    if not exe:
        print("[launch_game] ERROR: Minecraft.Windows.exe not found.")
        sys.exit(1)

    if args.config:
        config_path = os.path.abspath(args.config)
    else:
        if args.project:
            project_root = os.path.abspath(args.project)
        elif os.path.isfile(os.path.join(os.getcwd(), "studio.json")):
            project_root = os.getcwd()
        else:
            sync_cmd = os.path.join(_PROJECT_ROOT, "sync_to_test.cmd")
            if os.path.isfile(sync_cmd):
                target_root = None
                with open(sync_cmd, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("set") and "TARGET_ROOT=" in line and "TARGET_UI_ROOT" not in line:
                            val = line.split("TARGET_ROOT=", 1)[1].strip().strip('"')
                            target_root = os.path.dirname(val)
                            break
                if target_root and os.path.isfile(os.path.join(target_root, "studio.json")):
                    print("[launch_game] detected pyreact framework dir.")
                    print("[launch_game] addon project is at: %s" % target_root)
                    print("[launch_game] re-run from there, or pass --project explicitly.")
                    sys.exit(0)
            project_root = _PROJECT_ROOT
        config_path = find_latest_cppconfig(project_root)
        if not config_path:
            print("[launch_game] no .cppconfig found, generating one...")
            config_path = setup_runtime(project_root)
        print("[launch_game] using config: %s" % config_path)

    port = args.port if args.port else _find_free_port()

    import tempfile
    if not args.log_output:
        log_dir = os.path.join(tempfile.gettempdir(), "pyreact-debug")
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        args.log_output = os.path.join(log_dir, "pyreact_game_%d.log" % port)

    CREATE_NO_WINDOW = 0x08000000
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    CREATE_NEW_CONSOLE = 0x00000010

    game_proc = subprocess.Popen(
        [exe,
         "config=%s" % config_path,
         "loggingIP=localhost",
         "loggingPort=%d" % port],
        creationflags=CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    server_cmd = [sys.executable, os.path.join(_SCRIPT_DIR, "log_server.py"),
                  "--port", str(port),
                  "--game-pid", str(game_proc.pid),
                  "--output", args.log_output]

    subprocess.Popen(
        server_cmd,
        creationflags=CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("[launch_game] game launched.")
    print("[launch_game] log server port: %d" % port)
    print("[launch_game] log file: %s" % args.log_output)
    print("[launch_game] waiting for AppReady signal (max 60s)...")

    # Give log_server a moment to bind its HTTP port
    time.sleep(1.5)

    if _poll_ready(port, time.time() + 60):
        print("[launch_game] AppReady received, done.")
    else:
        print("[launch_game] timeout. Game continues running on port %d." % port)


if __name__ == "__main__":
    main()
