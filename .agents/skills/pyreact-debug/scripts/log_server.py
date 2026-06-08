# -*- coding: utf-8 -*-
"""
TCP log server that receives game logs from Minecraft.Windows.exe.

Persists for the entire session (does NOT exit when game dies).
Exposes an HTTP API on port+1 for log retrieval and command sending.

HTTP API:
  GET  /logs?since=N&grep=PATTERN&ignore_case=1   -> JSON {lines: [...], total: N}
  POST /send_command  body: {"command": "..."}    -> JSON {sent: N}
  GET  /status                                    -> JSON {running: bool, game_pid: N|null}
"""

import argparse
import os
import socket
import threading
import sys
import json

_clients = []
_clients_lock = threading.Lock()

_log_lines = []       # list of str, in-memory log history
_log_lock = threading.RLock()

_READY_SIGNAL = '=====> PyreactRuntime AppReady:'


def _decode(data):
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return data.decode('gbk', errors='replace')


def _append_line(line, log_file, ready_file):
    with _log_lock:
        _log_lines.append(line)
    sys.stdout.write(line)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    if log_file:
        log_file.write(line)
        log_file.flush()
    if ready_file and _READY_SIGNAL in line:
        try:
            with open(ready_file, 'w') as rf:
                rf.write('ready\n')
        except Exception:
            pass


def _handle_client(sock, addr, log_file, ready_file):
    print("[log_server] client connected: %s:%d" % (addr[0], addr[1]))
    try:
        buf = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            buf += data
            while buf:
                if buf[0:1] == b'\xff':
                    end = buf.find(b'\xff', 1)
                    if end == -1:
                        break
                    msg = _decode(buf[1:end])
                    buf = buf[end + 1:]
                    line = "[cmd-msg] " + msg + "\n"
                else:
                    nl = buf.find(b'\n')
                    if nl == -1:
                        if len(buf) > 8192:
                            line = _decode(buf)
                            buf = b""
                        else:
                            break
                    else:
                        line = _decode(buf[:nl + 1])
                        buf = buf[nl + 1:]
                _append_line(line, log_file, ready_file)
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


def _watch_pid(pid, game_dead_event):
    import time
    try:
        import psutil
        p = psutil.Process(pid)
        while True:
            if not p.is_running() or p.status() == psutil.STATUS_ZOMBIE:
                break
            time.sleep(2)
    except Exception:
        import subprocess as _sp
        while True:
            try:
                out = _sp.check_output(
                    ['tasklist', '/FI', 'PID eq %d' % pid, '/NH'],
                    stderr=_sp.DEVNULL
                )
                if str(pid) not in out.decode('utf-8', errors='replace'):
                    break
            except Exception:
                break
            time.sleep(2)
    print("[log_server] game process %d exited" % pid)
    game_dead_event.set()


# ---------- HTTP server ----------

def _http_server(http_port, game_dead_event, game_pid_ref):
    """Minimal HTTP server on http_port (log TCP port + 1)."""
    import re
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", http_port))
    srv.listen(10)
    srv.settimeout(1.0)
    print("[log_server] HTTP API on port %d" % http_port)

    def handle(conn):
        try:
            raw = b""
            while b"\r\n\r\n" not in raw:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                raw += chunk
            header_part, _, body_buf = raw.partition(b"\r\n\r\n")
            header_text = header_part.decode('utf-8', errors='replace')
            lines = header_text.split('\r\n')
            req_line = lines[0]
            method, path_qs = req_line.split(' ', 1)[:2][0], req_line.split(' ', 2)[1] if ' ' in req_line else '/'

            # parse query string
            qs = {}
            if '?' in path_qs:
                path, query = path_qs.split('?', 1)
                for part in query.split('&'):
                    if '=' in part:
                        k, v = part.split('=', 1)
                        qs[k] = v
            else:
                path = path_qs.split(' ')[0]

            def respond(status, obj):
                body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
                resp = ("HTTP/1.1 %s\r\nContent-Type: application/json\r\nContent-Length: %d\r\nAccess-Control-Allow-Origin: *\r\n\r\n" % (status, len(body))).encode('utf-8') + body
                conn.sendall(resp)

            if path == '/logs':
                import re as _re
                since = int(qs.get('since', '0'))
                grep = qs.get('grep', None)
                if grep:
                    import urllib.parse
                    grep = urllib.parse.unquote_plus(grep)
                ignore_case = qs.get('ignore_case', '0') not in ('0', 'false', '')
                with _log_lock:
                    total = len(_log_lines)
                    selected = list(enumerate(_log_lines, 1))[since:]
                if grep:
                    flags = _re.IGNORECASE if ignore_case else 0
                    pat = _re.compile(grep, flags)
                    selected = [(i, l) for i, l in selected if pat.search(l)]
                respond("200 OK", {"lines": [{"n": i, "text": l} for i, l in selected], "total": total})

            elif path == '/send_command':
                # read body
                content_length = 0
                for h in lines[1:]:
                    if h.lower().startswith('content-length:'):
                        content_length = int(h.split(':', 1)[1].strip())
                body_bytes = body_buf
                while len(body_bytes) < content_length:
                    body_bytes += conn.recv(4096)
                try:
                    obj = json.loads(body_bytes.decode('utf-8'))
                    cmd = obj.get('command', '')
                    sent = send_command(cmd)
                    respond("200 OK", {"sent": sent})
                except Exception as e:
                    respond("400 Bad Request", {"error": str(e)})

            elif path == '/status':
                respond("200 OK", {
                    "game_alive": not game_dead_event.is_set(),
                    "game_pid": game_pid_ref[0],
                })

            else:
                respond("404 Not Found", {"error": "unknown path"})
        except Exception as e:
            print("[log_server] http handler error: %s" % e)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    while True:
        try:
            conn, _ = srv.accept()
            t = threading.Thread(target=handle, args=(conn,))
            t.daemon = True
            t.start()
        except socket.timeout:
            continue
        except Exception:
            break


def run(port, log_file=None, ready_file=None):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(5)
    server.settimeout(1.0)
    print("[log_server] listening on port %d" % port)
    try:
        while True:
            try:
                sock, addr = server.accept()
            except socket.timeout:
                continue
            with _clients_lock:
                _clients.append(sock)
            t = threading.Thread(target=_handle_client, args=(sock, addr, log_file, ready_file))
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
    parser.add_argument("--game-pid", type=int, default=None, help="Watch this PID (server stays up after it dies)")
    args = parser.parse_args()

    log_file = None
    if args.output:
        log_file = open(args.output, 'a', encoding='utf-8')

    game_dead_event = threading.Event()
    game_pid_ref = [args.game_pid]

    if args.game_pid:
        t = threading.Thread(target=_watch_pid, args=(args.game_pid, game_dead_event))
        t.daemon = True
        t.start()

    # HTTP API on port+1
    http_port = args.port + 1
    ht = threading.Thread(target=_http_server, args=(http_port, game_dead_event, game_pid_ref))
    ht.daemon = True
    ht.start()

    try:
        run(args.port, log_file=log_file, ready_file=args.ready_file)
    finally:
        if log_file:
            log_file.close()


if __name__ == "__main__":
    main()
