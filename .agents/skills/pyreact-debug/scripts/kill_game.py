# -*- coding: utf-8 -*-
"""
Kill all running Minecraft.Windows.exe processes.

Usage:
    python kill_game.py [--wait]
"""

import argparse
import sys


def kill_game(wait=False):
    try:
        import psutil
    except ImportError:
        print("[kill_game] psutil not installed. Run: pip install psutil")
        sys.exit(1)

    killed = []
    for proc in psutil.process_iter(['name', 'pid']):
        if proc.info['name'] == 'Minecraft.Windows.exe':
            try:
                proc.kill()
                killed.append(proc.info['pid'])
            except Exception as e:
                print("[kill_game] failed to kill pid %d: %s" % (proc.info['pid'], e))

    if not killed:
        print("[kill_game] no Minecraft.Windows.exe process found")
        return False

    print("[kill_game] killed pids: %s" % killed)

    if wait:
        import time
        for _ in range(30):
            still = [p for p in psutil.process_iter(['name']) if p.info['name'] == 'Minecraft.Windows.exe']
            if not still:
                break
            time.sleep(0.5)

    return True


def main():
    parser = argparse.ArgumentParser(description="Kill Minecraft game process")
    parser.add_argument("--wait", action="store_true", help="Wait until process is gone")
    args = parser.parse_args()
    ok = kill_game(wait=args.wait)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
