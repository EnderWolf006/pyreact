# -*- coding: utf-8 -*-
"""
Performance profiling helpers.

Usage:
    python perf.py --port PORT start          # begin_performance_profile + start_profile
    python perf.py --port PORT stop           # end_performance_profile + stop_profile + log
    python perf.py --port PORT script-start   # start_profile only
    python perf.py --port PORT script-stop    # stop_profile only
    python perf.py --port PORT mem-start      # start_mem_profile
    python perf.py --port PORT mem-stop       # stop_mem_profile
    python perf.py --port PORT dump           # log_performance_profile_data
"""

import argparse
import sys

from send_command import send_command

_ACTIONS = {
    'start':        ['begin_performance_profile', 'start_profile'],
    'stop':         ['end_performance_profile', 'stop_profile', 'log_performance_profile_data'],
    'script-start': ['start_profile'],
    'script-stop':  ['stop_profile'],
    'mem-start':    ['start_mem_profile'],
    'mem-stop':     ['stop_mem_profile'],
    'dump':         ['log_performance_profile_data'],
}


def main():
    parser = argparse.ArgumentParser(description="Pyreact game performance commands")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("action", choices=sorted(_ACTIONS.keys()))
    args = parser.parse_args()

    commands = _ACTIONS[args.action]
    ok = True
    for cmd in commands:
        if not send_command(args.host, args.port, cmd):
            ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
