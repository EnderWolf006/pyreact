# -*- coding: utf-8 -*-
"""
TCP log server that receives game logs streamed from Minecraft.Windows.exe.

Usage:
    python log_server.py [--port PORT] [--output FILE]

The game must be launched with:
    Minecraft.Windows.exe ... loggingIP=localhost loggingPort=<PORT>

By default prints logs to stdout. Use --output to also write to a file.
The server also accepts reverse commands (see send_command.py).
"""

import argparse
import os
import socket
import threading
import sys

_clients = []
_clients_lock = threading.Lock()

_READY_SIGNAL = '=====> PyreactRuntime AppReady:'


def _handle_client(sock, addr, log_file, stop_event=None, ready_file=None):
    print("[log_server] client connected: %s:%d" % (addr[0], addr[1]))
    try:
        buf = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            buf += data
            # command messages are framed with 0xFF ... 0xFF
            while buf:
                if buf[0:1] == b'\xff':
                    end = buf.find(b'\xff', 1)
                    if end == -1:
                        break
                    msg = buf[1:end].decode('utf-8', errors='replace')
                    buf = buf[end + 1:]
                    line = "[cmd-msg] " + msg + "\n"
                else:
                    nl = buf.find(b'\n')
                    if nl == -1:
                        if len(buf) > 8192:
                            line = buf.decode('utf-8', errors='replace')
                            buf = b""
                        else:
                            break
                    else:
                        line = buf[:nl + 1].decode('utf-8', errors='replace')
                        buf = buf[nl + 1:]
                sys.stdout.write(line)
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
                if log_file:
                    log_file.write(line)
                    log_file.flush()
                if stop_event and _READY_SIGNAL in line:
                    stop_event.set()
                if ready_file and _READY_SIGNAL in line:
                    try:
                        with open(ready_file, 'w') as rf:
                            rf.write('ready\n')
                    except Exception:
                        pass
    except Exception as e:
        print("[log_server] client error: %s" % e)
    finally:
        with _clients_lock:
            _clients[:] = [c for c in _clients if c is not sock]
        try:
            sock.close()
        except Exception:
            pass
        print("[log_server] client disconnected: %s:%d" % (addr[0], addr[1]))


def send_command(command):
    """Send a null-terminated command to all connected game clients."""
    payload = (command + "\x00").encode('utf-8')
    with _clients_lock:
        targets = list(_clients)
    sent = 0
    for sock in targets:
        try:
            sock.sendall(payload)
            sent += 1
        except Exception as e:
            print("[log_server] send_command failed: %s" % e)
    return sent


def _watch_pid(pid, stop_event):
    """Exit when the watched process dies."""
    import time
    try:
        import psutil
        p = psutil.Process(pid)
        while not stop_event.is_set():
            if not p.is_running() or p.status() == psutil.STATUS_ZOMBIE:
                break
            time.sleep(2)
    except Exception:
        # Fallback: poll via os.kill(pid, 0)
        import time
        while not stop_event.is_set():
            try:
                os.kill(pid, 0)
            except OSError:
                break
            time.sleep(2)
    stop_event.set()


def run(port, log_file=None, stop_event=None, ready_file=None):
    if stop_event is None:
        import threading as _threading
        stop_event = _threading.Event()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(5)
    server.settimeout(1.0)
    print("[log_server] listening on port %d" % port)
    try:
        while not (stop_event and stop_event.is_set()):
            try:
                sock, addr = server.accept()
            except socket.timeout:
                continue
            with _clients_lock:
                _clients.append(sock)
            t = threading.Thread(target=_handle_client, args=(sock, addr, log_file, stop_event, ready_file))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\n[log_server] stopped")
    finally:
        server.close()


def main():
    parser = argparse.ArgumentParser(description="Pyreact game log server")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--output", default=None)
    parser.add_argument("--ready-file", default=None)
    parser.add_argument("--game-pid", type=int, default=None, help="Exit when this PID dies")
    args = parser.parse_args()

    import threading
    stop_event = threading.Event()

    log_file = None
    if args.output:
        log_file = open(args.output, 'a', encoding='utf-8')

    if args.game_pid:
        t = threading.Thread(target=_watch_pid, args=(args.game_pid, stop_event))
        t.daemon = True
        t.start()

    try:
        run(args.port, log_file=log_file, stop_event=stop_event, ready_file=args.ready_file)
    finally:
        if log_file:
            log_file.close()


if __name__ == "__main__":
    main()
