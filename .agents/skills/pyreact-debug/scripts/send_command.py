# -*- coding: utf-8 -*-
"""
Send a studio command to connected game clients via the log server's TCP connection.

Usage:
    python send_command.py --host HOST --port PORT <command> [args...]

Common commands:
    reload_pack                  Hot-reload behavior pack scripts
    reload_cache                 Hot-reload from pack cache
    restart_local_game           Reload the current world
    begin_performance_profile    Start perf profiling
    end_performance_profile      Stop perf profiling
    log_performance_profile_data Print perf data to game log
    start_profile                Start script profiling
    stop_profile                 Stop script profiling
    start_mem_profile            Start memory profiling
    stop_mem_profile             Stop memory profiling
    create_world                 Create a new world
    release_mouse                Release mouse capture

UI inspection commands (write result to clipboard in-game):
    pyreact_dump_tree [app_id]           Dump full UI tree to clipboard
    pyreact_dump_subtree <node_id> [app_id]  Dump subtree to clipboard
    pyreact_dump_node <node_id> [app_id]     Dump single node props to clipboard

Examples:
    python send_command.py --port 8765 reload_pack
    python send_command.py --port 8765 pyreact_dump_tree my_app_id
"""

import argparse
import socket
import sys


def send_command(host, port, command):
    payload = (command + "\x00").encode('utf-8')
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.sendall(payload)
        sock.close()
        print("[send_command] sent: %r" % command)
        return True
    except Exception as e:
        print("[send_command] ERROR: %s" % e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Send studio command to game")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("command", nargs="+", help="Command and optional arguments")
    args = parser.parse_args()

    command = " ".join(args.command)
    ok = send_command(args.host, args.port, command)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
