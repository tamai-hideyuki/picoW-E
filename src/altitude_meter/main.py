import network
import ntptime
import time
import gc
from machine import Pin, I2C, Timer
import ssd1306
import bme280
import config
from altitude import calculate_altitude, format_altitude
from server import Server


class Sensor:
    def __init__(self):
        i2c = I2C(0, sda=Pin(config.I2C_SDA_PIN), scl=Pin(config.I2C_SCL_PIN))
        self.bme = bme280.BME280(i2c=i2c)
        self._ring = [None] * config.RING_BUFFER_SIZE
        self._ring_idx = 0
        self._ring_count = 0
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
        except Exception:
            pass

    def start(self):
        self._timer.init(
            period=config.SENSOR_INTERVAL_SEC * 1000,
            mode=Timer.PERIODIC,
            callback=self._sample,
        )

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
        result = []
        if self._ring_count < config.RING_BUFFER_SIZE:
            start = 0
        else:
            start = self._ring_idx
        for i in range(self._ring_count):
            e = self._ring[(start + i) % config.RING_BUFFER_SIZE]
            if e[0] >= cutoff:
                result.append(e)
        return result

    def buffer_len(self):
        return self._ring_count


def connect_wifi(oled, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.SSID, config.PASSWORD)

    oled.fill(0)
    oled.text("Connecting...", 0, 0)
    oled.show()

    for i in range(timeout):
        if wlan.isconnected():
            return wlan.ifconfig()[0]
        oled.fill(0)
        oled.text("Connecting...", 0, 0)
        oled.text("{}s / {}s".format(i + 1, timeout), 0, 16)
        oled.show()
        time.sleep(1)

    oled.fill(0)
    oled.text("WiFi FAILED", 0, 0)
    oled.show()
    return None


def sync_time():
    try:
        ntptime.settime()
        print("NTP sync OK")
    except Exception:
        print("NTP sync failed")


def main():
    i2c = I2C(0, sda=Pin(config.I2C_SDA_PIN), scl=Pin(config.I2C_SCL_PIN))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)

    ip = connect_wifi(oled)
    if ip is None:
        print("WiFi connection failed. Rebooting in 5s...")
        time.sleep(5)
        import machine
        machine.reset()
    print("Connected:", ip)

    sync_time()

    sensor = Sensor()
    sensor.start()
    print("Sensor started (every {}s)".format(config.SENSOR_INTERVAL_SEC))

    srv = Server(sensor)
    srv.setup()

    oled.fill(0)
    oled.text("Altitude Meter", 0, 0)
    oled.text(ip, 0, 16)
    oled.text("Ready", 0, 32)
    oled.show()

    gc.collect()
    print("Free mem:", gc.mem_free())

    gc_interval = 30
    last_gc = time.time()
    last_oled = 0

    while True:
        srv.handle_one()

        now = time.time()

        # OLEDに高度を表示（3秒ごと更新）
        if now - last_oled >= 3:
            entry = sensor.current()
            if entry:
                _, temp, humi, pres = entry
                alt = calculate_altitude(pres, temp, humi)
                oled.fill(0)
                oled.text("Altitude Meter", 0, 0)
                oled.text(format_altitude(alt), 0, 20)
                oled.text("{:.1f}C {:.0f}% {:.0f}hPa".format(temp, humi, pres), 0, 40)
                oled.text(ip, 0, 54)
                oled.show()
            last_oled = now

        if now - last_gc >= gc_interval:
            gc.collect()
            last_gc = now


main()
