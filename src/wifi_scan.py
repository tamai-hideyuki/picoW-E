from machine import Pin, I2C
import ssd1306
import network
import time

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)
oled.text("Scanning...", 0, 0)
oled.show()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
nets = wlan.scan()

oled.fill(0)
oled.text("Found:", 0, 0)
oled.text(str(len(nets)), 0, 16)
oled.text("networks!", 0, 32)
oled.show()

print("スキャン結果:")
for net in nets:
    print(net[0], net[3])
