import socket
import time
import json
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


def _json_response(data):
    body = json.dumps(data)
    return (
        "HTTP/1.0 200 OK\r\n"
        "Content-Type: application/json\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "\r\n" + body
    )


def _html_response(body):
    return (
        "HTTP/1.0 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n" + body
    )


def _format_time(ts):
    t = time.localtime(ts + config.TZ_OFFSET)
    return "{:02d}:{:02d}".format(t[3], t[4])


class Server:
    def __init__(self, sensor):
        self.sensor = sensor

    def _handle_api_current(self):
        entry = self.sensor.current()
        data = {"timestamp": entry[0], "temp": entry[1], "humi": entry[2], "pres": entry[3]}
        return _json_response(data)

    def _handle_api_history(self, params):
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

        data = [[_format_time(r[0]), r[1], r[2], r[3]] for r in records]
        return _json_response({"range": range_val, "source": source, "data": data})

    def _handle_api_status(self):
        files = data_store.list_data_files()
        usage = data_store.disk_usage()
        data = {
            "files": files,
            "disk_bytes": usage,
            "buffer_len": len(self.sensor.buffer),
            "uptime": time.time(),
        }
        return _json_response(data)

    def handle(self, conn):
        try:
            conn.settimeout(3)
            data = conn.recv(1024).decode("utf-8")
            if not data:
                return
            method, raw_path = _parse_request(data)
            path, params = _parse_query(raw_path)

            if path == "/api/current":
                response = self._handle_api_current()
            elif path == "/api/history":
                response = self._handle_api_history(params)
            elif path == "/api/status":
                response = self._handle_api_status()
            elif path == "/favicon.ico":
                response = "HTTP/1.0 204 No Content\r\n\r\n"
            else:
                response = _html_response(DASHBOARD)

            conn.sendall(response)
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
        try:
            conn, addr = self._sock.accept()
            self.handle(conn)
        except OSError:
            pass
