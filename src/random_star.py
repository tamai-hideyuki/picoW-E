from machine import Pin, I2C
import ssd1306
import random
import time

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

while True:
	oled.fill(0)
	x = random.randint(0, 120)
	y = random.randint(0, 56)
	oled.text("*", x, y)
	oled.show()
	time.sleep(0.2)
