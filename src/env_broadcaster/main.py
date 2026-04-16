import network
import ntptime
import time
import gc
from machine import Pin, I2C
import ssd1306
import config
from sensor import Sensor
from broadcaster import Broadcaster


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

    sensor = Sensor(i2c)
    broadcaster = Broadcaster(config.BROADCAST_ADDR, config.BROADCAST_PORT)

    oled.fill(0)
    oled.text("UDP Broadcast", 0, 0)
    oled.text(ip, 0, 16)
    oled.text("port:{}".format(config.BROADCAST_PORT), 0, 32)
    oled.show()

    print("Broadcasting to {}:{} every {}s".format(
        config.BROADCAST_ADDR, config.BROADCAST_PORT, config.BROADCAST_INTERVAL_SEC
    ))

    sent = 0
    while True:
        reading = sensor.read()
        if reading is not None:
            temp, humi, pres = reading
            payload = {
                "device": config.DEVICE_ID,
                "ts": time.time(),
                "temp_c": round(temp, 2),
                "humidity": round(humi, 2),
                "pressure_hpa": round(pres, 2),
            }
            try:
                broadcaster.send(payload)
                sent += 1
            except OSError as e:
                print("Send failed:", e)

            oled.fill(0)
            oled.text("UDP Broadcast", 0, 0)
            oled.text(ip, 0, 16)
            oled.text("sent: {}".format(sent), 0, 32)
            oled.text("T:{:.1f} H:{:.0f}".format(temp, humi), 0, 48)
            oled.show()

        gc.collect()
        time.sleep(config.BROADCAST_INTERVAL_SEC)


main()
