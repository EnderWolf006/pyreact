# -*- coding: utf-8 -*-
"""
Simulate button click or input text via clipboard trigger.

Usage:
    python simulate.py click  --node-id <node_id> [--app-id <app_id>] [--timeout N]
    python simulate.py input  --node-id <node_id> --text <text> [--app-id <app_id>] [--timeout N]
"""

import argparse
import json
import subprocess
import sys
import time


def _write_clipboard(text):
    proc = subprocess.Popen(
        ['powershell', '-Command', '$input | Set-Clipboard'],
        stdin=subprocess.PIPE
    )
    proc.communicate(input=text.encode('utf-8'))
    return proc.returncode == 0


def _read_clipboard():
    result = subprocess.run(
        ['powershell', '-Command', 'Get-Clipboard'],
        capture_output=True, text=True, timeout=5
    )
    return result.stdout.rstrip('\r\n')


def _wait_ack(timeout):
    """Wait until clipboard becomes __pyreact_ack__ (game consumed the trigger)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.2)
        if (_read_clipboard() or '').strip() == '__pyreact_ack__':
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Simulate Pyreact UI interactions via clipboard")
    parser.add_argument("action", choices=["click", "input"], help="Action to perform")
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--app-id", default=None)
    parser.add_argument("--text", default="", help="Text to set (for 'input' action)")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    params = {"node_id": args.node_id}
    if args.app_id:
        params["app_id"] = args.app_id

    if args.action == "click":
        cmd = "click"
    else:
        cmd = "set_input"
        params["text"] = args.text

    trigger = json.dumps({"pyreact_debug": cmd, "params": params}, ensure_ascii=False)
    print("[simulate] writing trigger: %s" % trigger)
    if not _write_clipboard(trigger):
        print("[simulate] ERROR: clipboard write failed")
        sys.exit(1)

    if _wait_ack(args.timeout):
        print("[simulate] OK: game consumed trigger")
    else:
        print("[simulate] WARNING: trigger may not have been consumed within %.1fs" % args.timeout)


if __name__ == "__main__":
    main()
