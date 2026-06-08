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

    import time

    TARGET_NAMES = {'Minecraft.Windows.exe', 'python.exe', 'pythonw.exe'}
    LOG_SERVER_SCRIPT = 'log_server.py'

    killed = []
    for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
        name = proc.info.get('name') or ''
        if name == 'Minecraft.Windows.exe':
            try:
                proc.kill()
                killed.append(('game', proc.info['pid']))
            except Exception as e:
                print("[kill_game] failed to kill game pid %d: %s" % (proc.info['pid'], e))
        elif name in ('python.exe', 'pythonw.exe'):
            cmdline = proc.info.get('cmdline') or []
            if any(LOG_SERVER_SCRIPT in (c or '') for c in cmdline):
                try:
                    proc.kill()
                    killed.append(('log_server', proc.info['pid']))
                except Exception as e:
                    print("[kill_game] failed to kill log_server pid %d: %s" % (proc.info['pid'], e))

    if not killed:
        print("[kill_game] no processes found")
        return False

    print("[kill_game] killed: %s" % killed)

    if wait:
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
