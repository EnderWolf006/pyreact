# -*- coding: utf-8 -*-
"""
Launch Minecraft.Windows.exe and start a log server.

Usage:
    python launch_game.py [--config <cppconfig_path>] [--port PORT] [--log-output FILE]

--config is optional: if omitted, the newest .cppconfig under <project root>/.runtime is used
(same convention as mcpywrap).

The script:
1. Finds Minecraft.Windows.exe via Windows registry
2. Starts the TCP log server in a background thread
3. Launches the game with loggingIP=localhost loggingPort=<PORT>
4. Streams game logs to stdout (and optionally a file)

Press Ctrl+C to stop the log server (the game keeps running).
"""

import argparse
import os
import subprocess
import socket
import sys

from _mcs import get_minecraft_exe, find_latest_cppconfig, setup_runtime
import log_server

# Project root = 4 levels up from this script:
# scripts/ -> pyreact-debug/ -> skills/ -> .agents/ -> project root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", "..", "..", ".."))


def _find_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def main():
    parser = argparse.ArgumentParser(description="Launch Minecraft game + log server")
    parser.add_argument("--config", default=None, help="Path to .cppconfig (auto-detected from .runtime if omitted)")
    parser.add_argument("--project", default=None, help="Addon project root containing studio.json (used when generating a new config)")
    parser.add_argument("--port", type=int, default=0, help="Log server port (0 = auto)")
    parser.add_argument("--log-output", default=None, help="Optional log file path")
    args = parser.parse_args()

    exe = get_minecraft_exe()
    if not exe:
        print("[launch_game] ERROR: Minecraft.Windows.exe not found. Is MC Studio installed?")
        sys.exit(1)

    if args.config:
        config_path = os.path.abspath(args.config)
    else:
        if args.project:
            project_root = os.path.abspath(args.project)
        elif os.path.isfile(os.path.join(os.getcwd(), "studio.json")):
            project_root = os.getcwd()
        else:
            # Check if we're in the pyreact framework dir - parse TARGET_ROOT from sync_to_test.cmd
            sync_cmd = os.path.join(_PROJECT_ROOT, "sync_to_test.cmd")
            if os.path.isfile(sync_cmd):
                target_root = None
                with open(sync_cmd, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("set") and "TARGET_ROOT=" in line and "TARGET_UI_ROOT" not in line:
                            # set "TARGET_ROOT=D:\path\..."
                            val = line.split("TARGET_ROOT=", 1)[1].strip().strip('"')
                            target_root = os.path.dirname(val)  # behavior_pack dir -> addon root
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

    log_file = None
    if args.log_output:
        log_file = open(args.log_output, 'a', encoding='utf-8')

    import threading
    server_ready = threading.Event()

    def _start_server():
        server_ready.set()
        log_server.run(port, log_file=log_file)

    t = threading.Thread(target=_start_server)
    t.daemon = True
    t.start()
    server_ready.wait()

    cmd = (
        'cmd /c start "MC Studio Game Console" '
        '"{exe}" config="{config}" loggingIP=localhost loggingPort={port}'
    ).format(exe=exe, config=config_path, port=port)

    print("[launch_game] starting game: %s" % exe)
    print("[launch_game] log server port: %d" % port)
    print("[launch_game] will detach in 30s (game keeps running)")
    subprocess.Popen(cmd, shell=True)

    try:
        t.join(timeout=30)
    except KeyboardInterrupt:
        pass
    finally:
        if log_file:
            log_file.close()
    print("[launch_game] detached. Game continues running on port %d." % port)


if __name__ == "__main__":
    main()
