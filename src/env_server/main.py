import network
import ntptime
import time
import gc
from machine import Pin, I2C
import ssd1306
import config
import data_store
from sensor import Sensor
from server import Server


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

    oled.fill(0)
    oled.text("Env Monitor", 0, 0)
    oled.text(ip, 0, 16)
    oled.text("Starting...", 0, 32)
    oled.show()

    sensor = Sensor()
    sensor.start()
    print("Sensor started (every {}s)".format(config.SENSOR_INTERVAL_SEC))

    srv = Server(sensor)
    srv.setup()

    oled.fill(0)
    oled.text("Env Monitor", 0, 0)
    oled.text(ip, 0, 16)
    oled.text("Server ready", 0, 32)
    oled.show()

    gc.collect()
    print("Free mem:", gc.mem_free())

    gc_interval = 30  # 30秒ごとに強制GC
    last_gc = time.time()

    while True:
        srv.handle_one()

        if sensor.pending_aggregate:
            data_store.save_record(*sensor.pending_aggregate)
            sensor.pending_aggregate = None
            gc.collect()
            last_gc = time.time()

        now = time.time()
        if now - last_gc >= gc_interval:
            gc.collect()
            last_gc = now

main()
