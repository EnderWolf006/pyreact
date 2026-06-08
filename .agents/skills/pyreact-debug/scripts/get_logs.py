# -*- coding: utf-8 -*-
"""
Read game logs from the log_server HTTP API.

Usage:
    python get_logs.py [--port PORT]
                       [--tail N | --head N | --lines START[-END] | --since LINENUM]
                       [--grep PATTERN] [--ignore-case]
"""

import argparse
import re
import sys
try:
    from urllib.request import urlopen
    from urllib.parse import urlencode
except ImportError:
    from urllib2 import urlopen
    from urllib import urlencode
import json


def fetch_logs(port, since=0, grep=None, ignore_case=False):
    params = {"since": since}
    if grep:
        params["grep"] = grep
    if ignore_case:
        params["ignore_case"] = "1"
    url = "http://localhost:%d/logs?%s" % (port + 1, urlencode(params))
    try:
        resp = urlopen(url, timeout=5)
        return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print("[get_logs] ERROR: cannot reach log_server on port %d: %s" % (port + 1, e))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Read Pyreact game logs from log_server")
    parser.add_argument("--port", type=int, required=True, help="Log server port (launch_game.py output)")
    parser.add_argument("--tail", type=int, default=None, metavar="N")
    parser.add_argument("--head", type=int, default=None, metavar="N")
    parser.add_argument("--lines", default=None, metavar="START[-END]")
    parser.add_argument("--since", type=int, default=None, metavar="LINENUM")
    parser.add_argument("--grep", default=None, metavar="PATTERN")
    parser.add_argument("--ignore-case", action="store_true")
    args = parser.parse_args()

    data = fetch_logs(args.port, grep=args.grep, ignore_case=args.ignore_case)
    total = data["total"]
    all_lines = data["lines"]  # list of {n, text}

    # Line range selection
    if args.lines:
        parts = args.lines.split("-")
        start = max(1, int(parts[0]))
        end = int(parts[1]) if len(parts) > 1 else total
        lines = [e for e in all_lines if start <= e["n"] <= end]
    elif args.since:
        lines = [e for e in all_lines if e["n"] >= max(1, args.since)]
    elif args.head:
        lines = all_lines[:args.head]
    elif args.tail:
        lines = all_lines[-args.tail:]
    else:
        lines = all_lines

    if not lines:
        print("[get_logs] no matching lines.")
        return

    print("[get_logs] %d lines (total: %d)\n" % (len(lines), total))
    for entry in lines:
        sys.stdout.write("%6d: %s" % (entry["n"], entry["text"]))
    if lines and not lines[-1]["text"].endswith("\n"):
        print()


if __name__ == "__main__":
    main()
