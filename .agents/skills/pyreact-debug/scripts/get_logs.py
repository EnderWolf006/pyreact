# -*- coding: utf-8 -*-
"""
Read game logs written by log_server.py.

Usage:
    python get_logs.py [--port PORT] [--file FILE]
                       [--tail N] [--head N] [--lines START[-END]]
                       [--grep PATTERN] [--ignore-case]
                       [--since LINENUM]

Examples:
    python get_logs.py --tail 50
    python get_logs.py --lines 100-200
    python get_logs.py --grep "PyreactRuntime"
    python get_logs.py --tail 100 --grep "ERROR" --ignore-case
    python get_logs.py --since 500          # lines 500 onwards
"""

import argparse
import os
import re
import sys
import tempfile


def _find_log(port):
    """Return the default log path for a given port."""
    return os.path.join(tempfile.gettempdir(), "pyreact_game_%d.log" % port)


def _latest_log():
    """Find the most recently modified pyreact_game_*.log in %TEMP%."""
    tmp = tempfile.gettempdir()
    candidates = [
        os.path.join(tmp, f)
        for f in os.listdir(tmp)
        if f.startswith("pyreact_game_") and f.endswith(".log")
    ]
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def main():
    parser = argparse.ArgumentParser(description="Read Pyreact game logs")
    parser.add_argument("--port", type=int, default=None, help="Port used when launching (auto-detects latest if omitted)")
    parser.add_argument("--file", default=None, help="Explicit log file path")
    parser.add_argument("--tail", type=int, default=None, metavar="N", help="Last N lines")
    parser.add_argument("--head", type=int, default=None, metavar="N", help="First N lines")
    parser.add_argument("--lines", default=None, metavar="START[-END]", help="Line range, 1-based (e.g. 100-200 or 300)")
    parser.add_argument("--since", type=int, default=None, metavar="LINENUM", help="Lines from LINENUM onwards (1-based)")
    parser.add_argument("--grep", default=None, metavar="PATTERN", help="Regex filter")
    parser.add_argument("--ignore-case", action="store_true")
    args = parser.parse_args()

    # Resolve log file
    if args.file:
        log_path = args.file
    elif args.port:
        log_path = _find_log(args.port)
    else:
        log_path = _latest_log()

    if not log_path or not os.path.isfile(log_path):
        print("[get_logs] ERROR: log file not found: %s" % log_path)
        print("[get_logs] Launch the game first with launch_game.py")
        sys.exit(1)

    print("[get_logs] reading: %s" % log_path)

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    total = len(all_lines)

    # --- Line range selection ---
    if args.lines:
        parts = args.lines.split("-")
        start = max(1, int(parts[0]))
        end = int(parts[1]) if len(parts) > 1 else total
        lines = all_lines[start - 1:end]
        offset = start
    elif args.since:
        start = max(1, args.since)
        lines = all_lines[start - 1:]
        offset = start
    elif args.head:
        lines = all_lines[:args.head]
        offset = 1
    elif args.tail:
        lines = all_lines[-args.tail:]
        offset = total - len(lines) + 1
    else:
        lines = all_lines
        offset = 1

    # --- Grep filter ---
    if args.grep:
        flags = re.IGNORECASE if args.ignore_case else 0
        pattern = re.compile(args.grep, flags)
        lines = [(i, l) for i, l in enumerate(lines, offset) if pattern.search(l)]
    else:
        lines = list(enumerate(lines, offset))

    if not lines:
        print("[get_logs] no matching lines.")
        return

    print("[get_logs] %d lines (total in file: %d)\n" % (len(lines), total))
    for lineno, text in lines:
        sys.stdout.write("%6d: %s" % (lineno, text))
    if not lines[-1][1].endswith("\n"):
        print()


if __name__ == "__main__":
    main()
