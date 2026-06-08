# -*- coding: utf-8 -*-
"""
Trigger in-game UI tree dump via clipboard, then read and print/save the result.

Usage:
    python get_ui_tree.py [--app-id APP_ID] [--node-id NODE_ID]
                          [--output FILE] [--timeout SECONDS]
                          [--quiet] [--json]

Default (no flags): fetches tree and prints pretty tree view.
--quiet: suppress stdout (file save still happens).
--json:  print raw JSON instead of pretty tree (ignored when --quiet).
"""

import argparse
import json
import os
import sys
import tempfile
import time

from clipboard_ipc import read_clipboard, write_clipboard
from print_ui_tree import print_tree


def _default_output():
    d = os.path.join(tempfile.gettempdir(), 'pyreact-debug')
    if not os.path.isdir(d):
        os.makedirs(d)
    return os.path.join(d, 'ui_tree.json')


def _wait_for_json_response(timeout):
    trigger = read_clipboard()
    deadline = time.time() + timeout
    ack_received = False
    while time.time() < deadline:
        time.sleep(0.1)
        content = read_clipboard()
        if content == trigger:
            continue
        if content and content.strip() == '__pyreact_ack__':
            if not ack_received:
                ack_received = True
                # game consumed trigger; give it 3s to write the JSON result
                deadline = min(deadline, time.time() + 3.0)
            continue
        if content:
            try:
                return json.loads(content)
            except (ValueError, TypeError):
                pass
    if ack_received:
        print("[get_ui_tree] ERROR: ack received but no JSON result (game-side dump may have failed)", file=sys.stderr)
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
    parser.add_argument("--json", action="store_true",
                        help="print raw JSON instead of pretty tree (ignored when --quiet)")
    args = parser.parse_args()

    params = {}
    if args.app_id:
        params['app_id'] = args.app_id
    if args.node_id:
        params['node_id'] = args.node_id
        cmd = 'dump_subtree'
    else:
        cmd = 'dump_tree'

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
    print("[get_ui_tree] saved to %s" % out_path, file=sys.stderr)

    if not args.quiet:
        print_tree(data, node_id=args.node_id, as_json=args.json)


if __name__ == "__main__":
    main()
