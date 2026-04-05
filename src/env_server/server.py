import socket
import time
import json
import gc
import config
import data_store
from html_template import DASHBOARD


def _parse_request(data):
    try:
        line = data.split("\r\n")[0]
        parts = line.split(" ")
        method = parts[0]
        path = parts[1]
        return method, path
    except Exception:
        return "GET", "/"


def _parse_query(path):
    params = {}
    if "?" in path:
        path, qs = path.split("?", 1)
        for pair in qs.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k] = v
    return path, params


def _format_time(ts):
    t = time.localtime(ts + config.TZ_OFFSET)
    return "{:02d}:{:02d}".format(t[3], t[4])


def _send_json(conn, data):
    """JSONレスポンスを送信（小さいデータ向け）"""
    body = json.dumps(data)
    conn.send("HTTP/1.0 200 OK\r\n"
              "Content-Type: application/json\r\n"
              "Connection: close\r\n"
              "Access-Control-Allow-Origin: *\r\n\r\n")
    conn.send(body)


def _send_html(conn, body):
    """HTMLレスポンスをチャンク送信"""
    conn.send("HTTP/1.0 200 OK\r\n"
              "Content-Type: text/html; charset=utf-8\r\n"
              "Connection: close\r\n\r\n")
    # 大きいHTMLを512バイトずつ送信（メモリ節約）
    mv = memoryview(body.encode("utf-8") if isinstance(body, str) else body)
    chunk = 512
    for i in range(0, len(mv), chunk):
        conn.send(mv[i:i + chunk])


def _send_history_json(conn, range_val, source, records):
    """履歴データをストリーミングJSON送信（巨大リストのjson.dumpsを回避）"""
    conn.send("HTTP/1.0 200 OK\r\n"
              "Content-Type: application/json\r\n"
              "Connection: close\r\n"
              "Access-Control-Allow-Origin: *\r\n\r\n")
    conn.send('{"range":"')
    conn.send(range_val)
    conn.send('","source":"')
    conn.send(source)
    conn.send('","data":[')

    first = True
    for r in records:
        t = _format_time(r[0])
        line = '["{}",{},{},{}]'.format(t, r[1], r[2], r[3])
        if first:
            first = False
        else:
            conn.send(",")
        conn.send(line)

    conn.send("]}")


class Server:
    def __init__(self, sensor):
        self.sensor = sensor
        self._request_count = 0

    def _handle_api_current(self, conn):
        entry = self.sensor.current()
        _send_json(conn, {
            "timestamp": entry[0],
            "temp": entry[1],
            "humi": entry[2],
            "pres": entry[3],
        })

    def _handle_api_history(self, conn, params):
        range_val = params.get("range", "24h")

        if range_val == "10m":
            records = self.sensor.recent(600)
            source = "buffer"
        elif range_val == "1h":
            cutoff = int(time.time() - 3600)
            buffer_data = self.sensor.recent(3600)
            file_data = data_store.load_records(since=cutoff)
            merged = sorted(set(file_data + buffer_data), key=lambda x: x[0])
            records = merged
            source = "buffer+file"
        else:
            records = data_store.load_records()
            source = "file"

        _send_history_json(conn, range_val, source, records)

    def _handle_api_status(self, conn):
        files = data_store.list_data_files()
        usage = data_store.disk_usage()
        _send_json(conn, {
            "files": files,
            "disk_bytes": usage,
            "buffer_len": self.sensor.buffer_len(),
            "free_mem": gc.mem_free(),
            "uptime": time.time(),
        })

    def handle(self, conn):
        try:
            conn.settimeout(2)
            data = conn.recv(1024).decode("utf-8")
            if not data:
                return
            method, raw_path = _parse_request(data)
            path, params = _parse_query(raw_path)

            if path == "/api/current":
                self._handle_api_current(conn)
            elif path == "/api/history":
                self._handle_api_history(conn, params)
            elif path == "/api/status":
                self._handle_api_status(conn)
            elif path == "/favicon.ico":
                conn.send("HTTP/1.0 204 No Content\r\nConnection: close\r\n\r\n")
            else:
                _send_html(conn, DASHBOARD)
        except Exception:
            try:
                conn.send("HTTP/1.0 500 Error\r\nConnection: close\r\n\r\n")
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def setup(self):
        addr = socket.getaddrinfo("0.0.0.0", config.SERVER_PORT)[0][-1]
        self._sock = socket.socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(addr)
        self._sock.listen(5)
        self._sock.settimeout(0)
        print("HTTP Server started on port", config.SERVER_PORT)

    def handle_one(self):
        """保留中の接続をまとめて処理する（最大4件）"""
        handled = 0
        for _ in range(4):
            try:
                conn, _ = self._sock.accept()
            except OSError:
                break
            self.handle(conn)
            handled += 1

        self._request_count += handled
        # 5リクエストごとにGC実行
        if handled > 0 and self._request_count >= 5:
            gc.collect()
            self._request_count = 0
