from machine import Pin, I2C
import ssd1306

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)
oled.rect(0, 0, 127, 63, 1)
oled.text("2026-4-3(Fri)", 16, 5)
oled.text("Hello!", 16, 16)
oled.text("Sonnet 4.6", 16, 32)
oled.text("ClaudeCode", 16, 48)
oled.show()
