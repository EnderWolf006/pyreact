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
import socket
import threading
import sys
import os

_clients = []
_clients_lock = threading.Lock()


def _handle_client(sock, addr, log_file):
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
                        # no newline yet, wait for more data unless looks like text
                        if len(buf) > 8192:
                            line = buf.decode('utf-8', errors='replace')
                            buf = b""
                        else:
                            break
                    else:
                        line = buf[:nl + 1].decode('utf-8', errors='replace')
                        buf = buf[nl + 1:]
                sys.stdout.write(line)
                sys.stdout.flush()
                if log_file:
                    log_file.write(line)
                    log_file.flush()
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


def run(port, log_file=None):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(5)
    print("[log_server] listening on port %d" % port)
    try:
        while True:
            sock, addr = server.accept()
            with _clients_lock:
                _clients.append(sock)
            t = threading.Thread(target=_handle_client, args=(sock, addr, log_file))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\n[log_server] stopped")
    finally:
        server.close()


def main():
    parser = argparse.ArgumentParser(description="Pyreact game log server")
    parser.add_argument("--port", type=int, default=8765, help="TCP port to listen on")
    parser.add_argument("--output", default=None, help="Optional log file path")
    args = parser.parse_args()

    log_file = None
    if args.output:
        log_file = open(args.output, 'a', encoding='utf-8')

    try:
        run(args.port, log_file=log_file)
    finally:
        if log_file:
            log_file.close()


if __name__ == "__main__":
    main()
