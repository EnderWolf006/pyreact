# -*- coding: utf-8 -*-
"""
Trigger in-game UI tree dump via clipboard, then read and print/save the result.

The game must be running (launch_game.py). This script writes a trigger JSON
to the clipboard; the game polls it each render tick, executes the dump, then
writes the result JSON back to the clipboard.

Usage:
    python get_ui_tree.py [--app-id APP_ID] [--output FILE] [--timeout SECONDS]
    python get_ui_tree.py --node-id NODE_ID [--app-id APP_ID] [--subtree] [--output FILE]

Options:
    --app-id    Target app_id (default: first mounted app)
    --node-id   Inspect a specific node (props only, or subtree with --subtree)
    --subtree   With --node-id: dump full subtree instead of props only
    --output    Save result JSON to file
    --timeout   Seconds to wait for clipboard update (default: 5)
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time


def _write_clipboard(text):
    try:
        proc = subprocess.Popen(
            ['powershell', '-Command', '$input | Set-Clipboard'],
            stdin=subprocess.PIPE
        )
        proc.communicate(input=text.encode('utf-8'))
        return proc.returncode == 0
    except Exception as e:
        print("[get_ui_tree] clipboard write error: %s" % e)
        return False


def _read_clipboard():
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-Clipboard'],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.rstrip('\r\n')
    except Exception as e:
        print("[get_ui_tree] clipboard read error: %s" % e)
        return None


def _wait_for_json_response(timeout):
    """Poll clipboard until it contains valid JSON different from our trigger, or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.3)
        content = _read_clipboard()
        if content and '"pyreact_debug"' not in content:
            try:
                return json.loads(content)
            except (ValueError, TypeError):
                pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Get Pyreact UI tree from game via clipboard")
    parser.add_argument("--app-id", default=None)
    parser.add_argument("--node-id", default=None, help="Inspect a specific node")
    parser.add_argument("--subtree", action="store_true", help="With --node-id: dump subtree")
    parser.add_argument("--output", default=None, help="Save result JSON to file (default: %%TEMP%%/pyreact_ui_tree.json)")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    params = {}
    if args.app_id:
        params['app_id'] = args.app_id

    if args.node_id:
        params['node_id'] = args.node_id
        cmd = 'dump_subtree' if args.subtree else 'dump_node'
    else:
        cmd = 'dump_tree'

    trigger = json.dumps({'pyreact_debug': cmd, 'params': params}, ensure_ascii=False)
    print("[get_ui_tree] writing trigger to clipboard: %s" % trigger)
    if not _write_clipboard(trigger):
        print("[get_ui_tree] ERROR: failed to write clipboard")
        sys.exit(1)

    print("[get_ui_tree] waiting for response (%.1fs)..." % args.timeout)
    data = _wait_for_json_response(args.timeout)

    if data is None:
        print("[get_ui_tree] ERROR: no valid JSON response in clipboard within %.1fs" % args.timeout)
        sys.exit(1)

    formatted = json.dumps(data, ensure_ascii=False, indent=2)
    print(formatted)

    out_path = args.output or os.path.join(tempfile.gettempdir(), 'pyreact_ui_tree.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(formatted)
    print("\n[get_ui_tree] saved to %s" % out_path)


if __name__ == "__main__":
    main()
