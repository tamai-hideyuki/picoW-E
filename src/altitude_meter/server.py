import socket
import json
import gc
import config
from altitude import calculate_altitude
from html_template import DASHBOARD


def _parse_request(data):
    try:
        line = data.split("\r\n")[0]
        parts = line.split(" ")
        return parts[0], parts[1]
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


def _send_json(conn, data):
    body = json.dumps(data)
    conn.send("HTTP/1.0 200 OK\r\n"
              "Content-Type: application/json\r\n"
              "Connection: close\r\n"
              "Access-Control-Allow-Origin: *\r\n\r\n")
    conn.send(body)


def _send_html(conn, body):
    conn.send("HTTP/1.0 200 OK\r\n"
              "Content-Type: text/html; charset=utf-8\r\n"
              "Connection: close\r\n\r\n")
    chunk = 256
    for i in range(0, len(body), chunk):
        conn.send(body[i:i + chunk])


def _send_history_json(conn, records):
    conn.send("HTTP/1.0 200 OK\r\n"
              "Content-Type: application/json\r\n"
              "Connection: close\r\n"
              "Access-Control-Allow-Origin: *\r\n\r\n")
    conn.send('{"data":[')

    first = True
    for r in records:
        line = '[{},{:.1f},{:.1f},{:.1f},{:.1f}]'.format(
            r[0], r[1], r[2], r[3], r[4])
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
        ts, temp, humi, pres = entry
        alt = calculate_altitude(pres, temp, humi)
        _send_json(conn, {
            "temp": round(temp, 1),
            "humi": round(humi, 1),
            "pres": round(pres, 1),
            "alt": round(alt, 1),
            "sea_level_pressure": config.SEA_LEVEL_PRESSURE,
            "pressure_offset": config.PRESSURE_OFFSET,
            "reference_altitude": config.REFERENCE_ALTITUDE,
        })

    def _handle_api_history(self, conn):
        records = self.sensor.recent(600)
        result = []
        for r in records:
            ts, temp, humi, pres = r
            alt = calculate_altitude(pres, temp, humi)
            result.append((ts, temp, humi, pres, alt))
        _send_history_json(conn, result)

    def _handle_api_set_pressure(self, conn, params):
        try:
            p = float(params.get("value", "1013.25"))
            config.SEA_LEVEL_PRESSURE = p + config.PRESSURE_OFFSET
            _send_json(conn, {
                "ok": True,
                "sea_level_pressure": config.SEA_LEVEL_PRESSURE,
                "pressure_offset": config.PRESSURE_OFFSET,
            })
        except ValueError:
            _send_json(conn, {"ok": False, "error": "invalid value"})

    def _handle_api_set_ref_alt(self, conn, params):
        try:
            alt = float(params.get("value", "73.0"))
            config.REFERENCE_ALTITUDE = alt
            _send_json(conn, {"ok": True, "reference_altitude": alt})
        except ValueError:
            _send_json(conn, {"ok": False, "error": "invalid value"})

    def _handle_api_calibrate(self, conn):
        entry = self.sensor.current()
        ts, temp, humi, pres = entry
        ref_alt = config.REFERENCE_ALTITUDE
        current_alt = calculate_altitude(pres, temp, humi)
        alt_error = current_alt - ref_alt
        offset = alt_error / 8.3
        config.PRESSURE_OFFSET = round(-offset, 2)
        config.SEA_LEVEL_PRESSURE = config.SEA_LEVEL_PRESSURE + config.PRESSURE_OFFSET
        new_alt = calculate_altitude(pres, temp, humi)
        _send_json(conn, {
            "ok": True,
            "reference_altitude": ref_alt,
            "before": round(current_alt, 1),
            "after": round(new_alt, 1),
            "pressure_offset": config.PRESSURE_OFFSET,
            "sea_level_pressure": config.SEA_LEVEL_PRESSURE,
        })

    def _handle_api_status(self, conn):
        _send_json(conn, {
            "buffer_len": self.sensor.buffer_len(),
            "free_mem": gc.mem_free(),
            "sea_level_pressure": config.SEA_LEVEL_PRESSURE,
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
                self._handle_api_history(conn)
            elif path == "/api/set_pressure":
                self._handle_api_set_pressure(conn, params)
            elif path == "/api/set_ref_alt":
                self._handle_api_set_ref_alt(conn, params)
            elif path == "/api/calibrate":
                self._handle_api_calibrate(conn)
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
        handled = 0
        for _ in range(4):
            try:
                conn, _ = self._sock.accept()
            except OSError:
                break
            self.handle(conn)
            handled += 1

        self._request_count += handled
        if handled > 0 and self._request_count >= 5:
            gc.collect()
            self._request_count = 0
