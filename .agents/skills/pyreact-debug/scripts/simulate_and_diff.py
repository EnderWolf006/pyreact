# -*- coding: utf-8 -*-
"""
Simulate a UI interaction and immediately diff the UI tree before/after.

Usage:
    python simulate_and_diff.py click  --node-id NODE_ID [--app-id APP_ID] [--timeout N] [--settle N] [--props] [--layout]
    python simulate_and_diff.py input  --node-id NODE_ID --text TEXT [--app-id APP_ID] [--timeout N] [--settle N] [--props] [--layout]

Workflow:
    1. Dump UI tree (before)
    2. Simulate click/input
    3. Wait --settle seconds for UI to stabilize
    4. Dump UI tree (after)
    5. Print diff to stdout
"""

import argparse
import json
import os
import sys
import tempfile
import time

from clipboard_ipc import read_clipboard, write_clipboard


# ── clipboard helpers ────────────────────────────────────────────────────────

def _clear():
    write_clipboard("")
    time.sleep(0.05)


def _wait_for_new_content(sentinel, timeout):
    """Wait until clipboard changes from sentinel value, return new content."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.2)
        content = read_clipboard()
        if content != sentinel:
            return content
    return None


def _wait_json(timeout):
    """Write trigger, then wait for game to respond with JSON."""
    # Clipboard was just set to the trigger JSON; wait for it to change
    trigger = read_clipboard()
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.2)
        content = read_clipboard()
        if content == trigger:
            continue  # game hasn't consumed trigger yet
        if content and content.strip() != "__pyreact_ack__":
            try:
                return json.loads(content)
            except (ValueError, TypeError):
                pass
    return None


def _wait_ack(timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.2)
        if (read_clipboard() or "").strip() == "__pyreact_ack__":
            return True
    return False


# ── tree helpers ──────────────────────────────────────────────────────────────

def _dump_tree(app_id, timeout):
    params = {}
    if app_id:
        params["app_id"] = app_id
    _clear()
    write_clipboard(json.dumps({"pyreact_debug": "dump_tree", "params": params}, ensure_ascii=False))
    return _wait_json(timeout)


def _flatten(node, path="", out=None):
    if out is None:
        out = {}
    node_id = node.get("id", "?")
    full_path = (path + "/" + node_id) if path else node_id
    out[full_path] = node
    for child in node.get("children", []):
        _flatten(child, full_path, out)
    return out


def _is_func_prop(v):
    """Return True if the value looks like a serialized function reference."""
    return isinstance(v, str) and v.startswith("<function ")


def _filter_props(props):
    return {k: v for k, v in props.items() if not _is_func_prop(v)}


def _node_summary(node, include_props, include_layout):
    parts = {"type": node.get("type")}
    if include_props:
        parts["props"] = _filter_props(node.get("props", {}))
    if include_layout:
        parts["layout"] = node.get("layout", {})
    return parts


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Simulate Pyreact UI interaction and diff tree before/after")
    parser.add_argument("action", choices=["click", "input"])
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--app-id", default=None)
    parser.add_argument("--text", default="")
    parser.add_argument("--timeout", type=float, default=5.0, help="seconds to wait for ack/tree response")
    parser.add_argument("--settle", type=float, default=0.5, help="seconds to wait after interaction before re-dump")
    parser.add_argument("--props", action="store_true", help="include props in diff output")
    parser.add_argument("--layout", action="store_true", help="include layout in diff output")
    parser.add_argument("--output-before", default=None, help="save before snapshot to file")
    parser.add_argument("--output-after", default=None, help="save after snapshot to file")
    args = parser.parse_args()

    tmp = os.path.join(tempfile.gettempdir(), "pyreact-debug")
    if not os.path.isdir(tmp):
        os.makedirs(tmp)

    # 1. before snapshot
    print("[simulate_and_diff] dumping tree (before)...", file=sys.stderr)
    before_data = _dump_tree(args.app_id, args.timeout)
    if before_data is None:
        print("[simulate_and_diff] ERROR: could not get before tree", file=sys.stderr)
        sys.exit(1)
    if args.output_before:
        with open(args.output_before, "wb") as f:
            f.write(json.dumps(before_data, ensure_ascii=False, indent=2).encode("utf-8"))

    # 2. simulate
    params = {"node_id": args.node_id}
    if args.app_id:
        params["app_id"] = args.app_id
    cmd = "click" if args.action == "click" else "set_input"
    if args.action == "input":
        params["text"] = args.text

    print("[simulate_and_diff] simulating %s on %s..." % (args.action, args.node_id), file=sys.stderr)
    _clear()
    write_clipboard(json.dumps({"pyreact_debug": cmd, "params": params}, ensure_ascii=False))
    if not _wait_ack(args.timeout):
        print("[simulate_and_diff] WARNING: ack not received within %.1fs" % args.timeout, file=sys.stderr)

    # 3. settle
    if args.settle > 0:
        time.sleep(args.settle)

    # 4. after snapshot
    print("[simulate_and_diff] dumping tree (after)...", file=sys.stderr)
    after_data = _dump_tree(args.app_id, args.timeout)
    if after_data is None:
        print("[simulate_and_diff] ERROR: could not get after tree", file=sys.stderr)
        sys.exit(1)
    if args.output_after:
        with open(args.output_after, "wb") as f:
            f.write(json.dumps(after_data, ensure_ascii=False, indent=2).encode("utf-8"))

    # 5. diff
    before_flat = _flatten(before_data.get("tree", before_data))
    after_flat = _flatten(after_data.get("tree", after_data))

    added = sorted(set(after_flat) - set(before_flat))
    removed = sorted(set(before_flat) - set(after_flat))
    changed = []
    for path in sorted(set(before_flat) & set(after_flat)):
        b = _node_summary(before_flat[path], args.props, args.layout)
        a = _node_summary(after_flat[path], args.props, args.layout)
        if b != a:
            changed.append({"path": path, "before": b, "after": a})

    result = {"added": added, "removed": removed, "changed": changed}
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print("[simulate_and_diff] +%d added, -%d removed, ~%d changed" % (len(added), len(removed), len(changed)), file=sys.stderr)


if __name__ == "__main__":
    main()
