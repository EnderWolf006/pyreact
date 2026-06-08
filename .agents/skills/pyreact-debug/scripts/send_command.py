# -*- coding: utf-8 -*-
"""
Send a studio command to the game via log_server HTTP API.

Usage:
    python send_command.py --port PORT <command> [args...]
"""

import argparse
import json
import sys

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request


def send_command(port, command):
    body = json.dumps({"command": command}).encode('utf-8')
    req = Request(
        "http://localhost:%d/send_command" % (port + 1),
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urlopen(req, timeout=5)
        data = json.loads(resp.read().decode('utf-8'))
        print("[send_command] sent: %r (delivered to %d client(s))" % (command, data.get("sent", 0)))
        return True
    except Exception as e:
        print("[send_command] ERROR: %s" % e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Send studio command to game via log_server")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("command", nargs="+")
    args = parser.parse_args()

    ok = send_command(args.port, " ".join(args.command))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
