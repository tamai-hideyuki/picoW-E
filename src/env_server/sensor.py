from machine import Pin, I2C, Timer
import bme280
import time
import config


class Sensor:
    def __init__(self):
        i2c = I2C(0, sda=Pin(config.I2C_SDA_PIN), scl=Pin(config.I2C_SCL_PIN))
        self.bme = bme280.BME280(i2c=i2c)
        # 固定長リングバッファ（pop(0)を避けてO(1)で回す）
        self._ring = [None] * config.RING_BUFFER_SIZE
        self._ring_idx = 0
        self._ring_count = 0
        self.aggregate_acc = []
        self.last_aggregate_time = time.time()
        self.pending_aggregate = None
        self._timer = Timer(-1)

    def read(self):
        try:
            values = self.bme.values
            temp = float(values[0].replace("C", "").strip())
            humi = float(values[2].replace("%", "").strip())
            pres = float(values[1].replace("hPa", "").strip())
            return temp, humi, pres
        except (ValueError, IndexError, OSError):
            return None

    def _sample(self, timer):
        try:
            now = time.time()
            result = self.read()
            if result is None:
                return
            temp, humi, pres = result
            entry = (now, temp, humi, pres)

            self._ring[self._ring_idx] = entry
            self._ring_idx = (self._ring_idx + 1) % config.RING_BUFFER_SIZE
            if self._ring_count < config.RING_BUFFER_SIZE:
                self._ring_count += 1

            self.aggregate_acc.append(entry)

            if now - self.last_aggregate_time >= config.AGGREGATE_INTERVAL_SEC:
                self._flush_aggregate()
                self.last_aggregate_time = now
        except Exception:
            pass

    def _flush_aggregate(self):
        if not self.aggregate_acc:
            return
        n = len(self.aggregate_acc)
        avg_time = self.aggregate_acc[n // 2][0]
        avg_temp = sum(e[1] for e in self.aggregate_acc) / n
        avg_humi = sum(e[2] for e in self.aggregate_acc) / n
        avg_pres = sum(e[3] for e in self.aggregate_acc) / n
        self.aggregate_acc = []
        self.pending_aggregate = (avg_time, avg_temp, avg_humi, avg_pres)

    def start(self):
        self._timer.init(
            period=config.SENSOR_INTERVAL_SEC * 1000,
            mode=Timer.PERIODIC,
            callback=self._sample,
        )

    def stop(self):
        self._timer.deinit()

    def _iter_buffer(self):
        """リングバッファを古い順にイテレートする"""
        if self._ring_count < config.RING_BUFFER_SIZE:
            start = 0
        else:
            start = self._ring_idx
        for i in range(self._ring_count):
            yield self._ring[(start + i) % config.RING_BUFFER_SIZE]

    def current(self):
        if self._ring_count > 0:
            last_idx = (self._ring_idx - 1) % config.RING_BUFFER_SIZE
            return self._ring[last_idx]
        now = time.time()
        result = self.read()
        if result is None:
            return (now, 0.0, 0.0, 0.0)
        return (now, result[0], result[1], result[2])

    def recent(self, seconds=600):
        cutoff = time.time() - seconds
        return [e for e in self._iter_buffer() if e[0] >= cutoff]

    def buffer_len(self):
        return self._ring_count
