# -*- coding: utf-8 -*-
"""
Print a saved UI tree JSON in ASCII-safe human-readable format.

Usage:
    python print_ui_tree.py [FILE] [--node-id NODE_ID] [--depth N] [--json]
"""

import argparse
import json
import os
import sys
import tempfile


def _key_info(node):
    """Return key prop string for display (content/src/item_name)."""
    props = node.get("props", {})
    node_type = node.get("type", "")
    if node_type == "Label" and "content" in props:
        v = props["content"]
        if v not in (None, ""):
            return u' "%s"' % v
    if node_type == "Image" and "src" in props:
        v = props["src"]
        if v not in (None, ""):
            return u' src=%s' % v
    if node_type == "Item" and "item_name" in props:
        v = props["item_name"]
        if v not in (None, ""):
            return u' item=%s' % v
    return u""


def _interactive(node):
    props = node.get("props", {})
    flags = []
    if "onClick" in props and props["onClick"] not in (None, False, ""):
        flags.append("clickable")
    node_type = node.get("type", "")
    if node_type == "Input":
        flags.append("input")
    elif node_type == "Button":
        if "clickable" not in flags:
            flags.append("clickable")
    return "|".join(flags)


def _print_node(node, prefix="", is_last=True, depth=None, current_depth=0):
    if depth is not None and current_depth > depth:
        return

    connector = "`-- " if is_last else "|-- "
    node_id = node.get("id", "?")
    node_type = node.get("type", "?")
    layout = node.get("layout", {})
    w = layout.get("width", "?")
    h = layout.get("height", "?")
    x = layout.get("x", "?")
    y = layout.get("y", "?")
    interactive = _interactive(node)
    interactive_str = " [%s]" % interactive if interactive else ""
    key_str = _key_info(node)

    line = u"%s%s%s (%s)%s %sx%s @(%s,%s)%s" % (
        prefix, connector, node_id, node_type, key_str, w, h, x, y, interactive_str
    )
    sys.stdout.buffer.write((line + "\n").encode("utf-8", errors="replace"))

    children = node.get("children", [])
    child_prefix = prefix + ("    " if is_last else "|   ")
    for i, child in enumerate(children):
        _print_node(child, child_prefix, i == len(children) - 1, depth, current_depth + 1)


def print_tree(data, node_id=None, depth=None, as_json=False):
    tree = data.get("tree", data)
    root = tree
    if node_id:
        def _find(node, nid):
            if node.get("id") == nid:
                return node
            for c in node.get("children", []):
                r = _find(c, nid)
                if r:
                    return r
            return None
        root = _find(tree, node_id)
        if root is None:
            print("[print_ui_tree] ERROR: node '%s' not found" % node_id, file=sys.stderr)
            sys.exit(1)

    if as_json:
        sys.stdout.buffer.write((json.dumps(root, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    else:
        _print_node(root, "", True, depth, 0)


def main():
    parser = argparse.ArgumentParser(description="Print Pyreact UI tree in ASCII-safe format")
    parser.add_argument("file", nargs="?", default=None)
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--depth", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="output raw JSON instead of tree")
    args = parser.parse_args()

    path = args.file or os.path.join(tempfile.gettempdir(), "pyreact-debug", "ui_tree.json")
    with open(path, "rb") as f:
        data = json.loads(f.read().decode("utf-8"))

    print_tree(data, node_id=args.node_id, depth=args.depth, as_json=args.json)


if __name__ == "__main__":
    main()
