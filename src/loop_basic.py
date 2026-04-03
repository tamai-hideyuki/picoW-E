from machine import Pin, I2C
import ssd1306
import time

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

count = 0
while True:
    oled.fill(0)
    oled.rect(0, 0, 127, 63, 1)
    oled.text("Count:", 8, 8)
    oled.text(str(count), 16, 32)
    oled.show()
    count += 1
    time.sleep(1)
