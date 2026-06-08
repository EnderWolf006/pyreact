# -*- coding: utf-8 -*-
"""
Compare two saved UI tree JSON files and report added/removed/changed nodes.

Usage:
    python diff_ui_tree.py <before.json> <after.json> [--props] [--layout]
"""

import argparse
import json
import sys


def _flatten(node, path="", out=None):
    if out is None:
        out = {}
    node_id = node.get("id", "?")
    full_path = (path + "/" + node_id) if path else node_id
    out[full_path] = node
    for child in node.get("children", []):
        _flatten(child, full_path, out)
    return out


def _node_summary(node, include_props, include_layout):
    parts = {"type": node.get("type")}
    if include_props:
        parts["props"] = node.get("props", {})
    if include_layout:
        parts["layout"] = node.get("layout", {})
    return parts


def _count_prop_changes(before_flat, after_flat):
    """Count nodes with props or layout changes (always computed)."""
    props_changed = 0
    layout_changed = 0
    for path in set(before_flat) & set(after_flat):
        b_node = before_flat[path]
        a_node = after_flat[path]
        if b_node.get("props") != a_node.get("props"):
            props_changed += 1
        if b_node.get("layout") != a_node.get("layout"):
            layout_changed += 1
    return props_changed, layout_changed


def main():
    parser = argparse.ArgumentParser(description="Diff two Pyreact UI tree JSON files")
    parser.add_argument("before", help="before snapshot JSON file")
    parser.add_argument("after", help="after snapshot JSON file")
    parser.add_argument("--props", action="store_true", help="include props in changed output")
    parser.add_argument("--layout", action="store_true", help="include layout in changed output")
    args = parser.parse_args()

    with open(args.before, encoding="utf-8") as f:
        before_tree = json.load(f)
    with open(args.after, encoding="utf-8") as f:
        after_tree = json.load(f)

    before = _flatten(before_tree)
    after = _flatten(after_tree)

    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = []
    for node_id in sorted(set(before) & set(after)):
        b = _node_summary(before[node_id], args.props, args.layout)
        a = _node_summary(after[node_id], args.props, args.layout)
        if b != a:
            changed.append({"id": node_id, "before": b, "after": a})

    result = {"added": added, "removed": removed, "changed": changed}
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    props_changed, layout_changed = _count_prop_changes(before, after)
    print("[diff_ui_tree] +%d added, -%d removed, ~%d changed" % (len(added), len(removed), len(changed)), file=sys.stderr)
    no_structural_changes = not added and not removed and not changed
    if no_structural_changes:
        if not args.props and props_changed:
            print("Note: props changed in %d node(s). Use --props to see details." % props_changed, file=sys.stderr)
        if not args.layout and layout_changed:
            print("Note: layout changed in %d node(s). Use --layout to see details." % layout_changed, file=sys.stderr)


if __name__ == "__main__":
    main()
