from machine import Pin, I2C
import ssd1306
import bme280
import time

# ハードウェアの初期化
i2c = I2C(0, sda=Pin(0), scl=Pin(1))  # I2C通信の設定
oled = ssd1306.SSD1306_I2C(128, 64, i2c)  # OLEDの初期化
bme = bme280.BME280(i2c=i2c)  # BME280の初期化

# 2秒ごとに永遠にループ
while True:
    oled.fill(0)          # 画面クリア
    oled.text("Temp.Humi.Pres", 0, 0)
    oled.text(bme.values[0], 0, 16)   # 温度
    oled.text(bme.values[2], 0, 32)  # 湿度
    oled.text(bme.values[1], 0, 48)  # 気圧
    oled.show()           # 画面に反映
    time.sleep(2)         # 2秒待つ
