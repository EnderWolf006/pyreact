# -*- coding: utf-8 -*-
"""
Trigger in-game UI tree dump via clipboard, then read and print/save the result.

Usage:
    python get_ui_tree.py [--app-id APP_ID] [--output FILE] [--timeout SECONDS]
    python get_ui_tree.py --node-id NODE_ID [--app-id APP_ID] [--subtree] [--output FILE]

Notes:
    - dump_node is NOT used: game-side serialization fails on non-JSON-serializable props
      (e.g. buttonBuilder functions). Always use dump_subtree to get a node and its children.
    - Default output: %TEMP%/pyreact-debug/ui_tree.json
    - Use --quiet to suppress stdout (avoids GBK encoding issues on Windows terminals).
      Then read the saved JSON file with open(path, 'rb').read().decode('utf-8').
"""

import argparse
import json
import os
import sys
import tempfile
import time

from clipboard_ipc import read_clipboard, write_clipboard


def _default_output():
    d = os.path.join(tempfile.gettempdir(), 'pyreact-debug')
    if not os.path.isdir(d):
        os.makedirs(d)
    return os.path.join(d, 'ui_tree.json')


def _wait_for_json_response(timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.3)
        content = read_clipboard()
        if content and '"pyreact_debug"' not in content and content.strip() != '__pyreact_ack__':
            try:
                return json.loads(content)
            except (ValueError, TypeError):
                pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Get Pyreact UI tree from game via clipboard")
    parser.add_argument("--app-id", default=None)
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--subtree", action="store_true",
                        help="(ignored, always uses subtree dump for node queries)")
    parser.add_argument("--output", default=None)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--quiet", action="store_true",
                        help="suppress stdout output (file save still happens)")
    args = parser.parse_args()

    params = {}
    if args.app_id:
        params['app_id'] = args.app_id
    if args.node_id:
        # Always use dump_subtree: dump_node fails when props contain non-serializable
        # objects (e.g. buttonBuilder). dump_subtree returns the node + children.
        params['node_id'] = args.node_id
        cmd = 'dump_subtree'
    else:
        cmd = 'dump_tree'

    # Clear clipboard before writing trigger so stale ack/data doesn't interfere
    write_clipboard('')
    time.sleep(0.05)

    trigger = json.dumps({'pyreact_debug': cmd, 'params': params}, ensure_ascii=False)
    print("[get_ui_tree] trigger: %s" % trigger)
    write_clipboard(trigger)

    print("[get_ui_tree] waiting for response (%.1fs)..." % args.timeout)
    data = _wait_for_json_response(args.timeout)

    if data is None:
        print("[get_ui_tree] ERROR: no valid JSON response within %.1fs" % args.timeout)
        sys.exit(1)

    out_path = args.output or _default_output()
    formatted = json.dumps(data, ensure_ascii=False, indent=2)
    with open(out_path, 'wb') as f:
        f.write(formatted.encode('utf-8'))

    if not args.quiet:
        sys.stdout.buffer.write((formatted + '\n').encode('utf-8'))
    print("[get_ui_tree] saved to %s" % out_path, file=sys.stderr)


if __name__ == "__main__":
    main()
