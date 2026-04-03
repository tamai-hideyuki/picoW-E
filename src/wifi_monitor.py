from machine import Pin, I2C
import ssd1306
import network
import time

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

while True:
    # スキャン中の表示
    oled.fill(0)
    oled.text("Scanning...", 0, 0)
    oled.show()

    nets = wlan.scan()

    # 1件ずつ表示
    for i, net in enumerate(nets):
        ssid = net[0].decode('utf-8', 'ignore')[:16]
        rssi = str(net[3])
        oled.fill(0)
        oled.text(ssid, 0, 0)
        oled.text(rssi + "dBm", 0, 16)
        oled.text(str(i+1)+"/"+str(len(nets)), 0, 48)
        oled.show()
        time.sleep(2)

    # 10秒待機
    oled.fill(0)
    oled.text("Wait 10sec...", 0, 0)
    oled.show()
    time.sleep(10)
