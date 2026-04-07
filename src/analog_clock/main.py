import network
import ntptime
import time
import math
from machine import Pin, I2C
import ssd1306
import bme280

# === 設定 ===
SSID = "Wi-Fi名"
PASSWORD = "パスワード"
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1
TZ_OFFSET = 9 * 3600  # JST

# 時計の中心と半径
CENTER_X = 31
CENTER_Y = 31
CLOCK_RADIUS = 22    # 文字盤
RING_RADIUS = 30     # 環境リング

# 環境リングの割り当て角度（12時位置 = -90度）
# 気温: 左上 (150〜270度)
# 湿度: 右上 (270〜390度 = 270〜30度)
# 気圧: 下  (30〜150度)
TEMPERATURE_RANGE = (0, 50)       # 気温 0〜50℃
HUMIDITY_RANGE = (0, 100)         # 湿度 0〜100%
PRESSURE_RANGE = (950, 1050)      # 気圧 950〜1050hPa


# === 描画関数 ===

def draw_line(oled, start_x, start_y, end_x, end_y, color=1):
    """ブレゼンハムの直線アルゴリズム"""
    delta_x = abs(end_x - start_x)
    delta_y = -abs(end_y - start_y)
    step_x = 1 if start_x < end_x else -1
    step_y = 1 if start_y < end_y else -1
    error = delta_x + delta_y
    while True:
        if 0 <= start_x < 128 and 0 <= start_y < 64:
            oled.pixel(start_x, start_y, color)
        if start_x == end_x and start_y == end_y:
            break
        double_error = 2 * error
        if double_error >= delta_y:
            error += delta_y
            start_x += step_x
        if double_error <= delta_x:
            error += delta_x
            start_y += step_y


def draw_circle(oled, center_x, center_y, radius, color=1):
    """ミッドポイント円アルゴリズム"""
    offset_x = radius
    offset_y = 0
    error = 1 - radius
    while offset_x >= offset_y:
        for mirror_x, mirror_y in [
                (offset_x, offset_y), (-offset_x, offset_y),
                (offset_x, -offset_y), (-offset_x, -offset_y),
                (offset_y, offset_x), (-offset_y, offset_x),
                (offset_y, -offset_x), (-offset_y, -offset_x)]:
            pixel_x = center_x + mirror_x
            pixel_y = center_y + mirror_y
            if 0 <= pixel_x < 128 and 0 <= pixel_y < 64:
                oled.pixel(pixel_x, pixel_y, color)
        offset_y += 1
        if error < 0:
            error += 2 * offset_y + 1
        else:
            offset_x -= 1
            error += 2 * (offset_y - offset_x) + 1


def draw_arc(oled, center_x, center_y, radius, start_degree, end_degree, color=1):
    step = 2
    for degree in range(start_degree, end_degree + 1, step):
        radian = math.radians(degree)
        pixel_x = int(center_x + radius * math.cos(radian))
        pixel_y = int(center_y + radius * math.sin(radian))
        if 0 <= pixel_x < 128 and 0 <= pixel_y < 64:
            oled.pixel(pixel_x, pixel_y, color)


def draw_thick_arc(oled, center_x, center_y, radius, start_degree, end_degree, color=1):
    for offset in range(3):
        draw_arc(oled, center_x, center_y, radius - offset, start_degree, end_degree, color)


def draw_hand(oled, center_x, center_y, length, angle_degree, color=1):
    radian = math.radians(angle_degree - 90)
    tip_x = int(center_x + length * math.cos(radian))
    tip_y = int(center_y + length * math.sin(radian))
    draw_line(oled, center_x, center_y, tip_x, tip_y, color)


def draw_hour_marks(oled, center_x, center_y, radius):
    for hour in range(12):
        angle = math.radians(hour * 30 - 90)
        inner_x = int(center_x + (radius - 2) * math.cos(angle))
        inner_y = int(center_y + (radius - 2) * math.sin(angle))
        outer_x = int(center_x + radius * math.cos(angle))
        outer_y = int(center_y + radius * math.sin(angle))
        draw_line(oled, inner_x, inner_y, outer_x, outer_y)


def value_to_arc_end(value, value_min, value_max, arc_start, arc_span):
    ratio = (value - value_min) / (value_max - value_min)
    ratio = max(0.0, min(1.0, ratio))
    return arc_start + int(arc_span * ratio)


def draw_environment_rings(oled, temperature, humidity, pressure):
    # 気温リング: 左上 (150〜270度)
    arc_start = 150
    arc_span = 120
    end = value_to_arc_end(temperature, TEMPERATURE_RANGE[0], TEMPERATURE_RANGE[1], arc_start, arc_span)
    draw_arc(oled, CENTER_X, CENTER_Y, RING_RADIUS, arc_start, arc_start + arc_span, color=1)
    if end > arc_start:
        draw_thick_arc(oled, CENTER_X, CENTER_Y, RING_RADIUS, arc_start, end, color=1)

    # 湿度リング: 右上 (270〜390度 → 270〜360 + 0〜30)
    arc_start2 = 270
    arc_span2 = 120
    end2 = value_to_arc_end(humidity, HUMIDITY_RANGE[0], HUMIDITY_RANGE[1], arc_start2, arc_span2)
    # 薄い円弧（ガイド）
    draw_arc(oled, CENTER_X, CENTER_Y, RING_RADIUS, 270, 360)
    draw_arc(oled, CENTER_X, CENTER_Y, RING_RADIUS, 0, 30)
    # 値の円弧（太い）
    if end2 > 360:
        draw_thick_arc(oled, CENTER_X, CENTER_Y, RING_RADIUS, 270, 360)
        draw_thick_arc(oled, CENTER_X, CENTER_Y, RING_RADIUS, 0, end2 - 360)
    elif end2 > arc_start2:
        draw_thick_arc(oled, CENTER_X, CENTER_Y, RING_RADIUS, arc_start2, end2)

    # 気圧リング: 下 (30〜150度)
    arc_start3 = 30
    arc_span3 = 120
    end3 = value_to_arc_end(pressure, PRESSURE_RANGE[0], PRESSURE_RANGE[1], arc_start3, arc_span3)
    draw_arc(oled, CENTER_X, CENTER_Y, RING_RADIUS, arc_start3, arc_start3 + arc_span3)
    if end3 > arc_start3:
        draw_thick_arc(oled, CENTER_X, CENTER_Y, RING_RADIUS, arc_start3, end3)


def draw_clock_face(oled, current_time):
    # 文字盤
    draw_circle(oled, CENTER_X, CENTER_Y, CLOCK_RADIUS)
    draw_hour_marks(oled, CENTER_X, CENTER_Y, CLOCK_RADIUS)

    # 針の角度
    second = current_time[5]
    minute = current_time[4]
    hour = current_time[3] % 12

    hour_angle = hour * 30 + minute * 0.5
    minute_angle = minute * 6 + second * 0.1
    second_angle = second * 6

    # 描画（時→分→秒の順で上に重ねる）
    draw_hand(oled, CENTER_X, CENTER_Y, 13, hour_angle)
    draw_hand(oled, CENTER_X, CENTER_Y, 19, minute_angle)
    draw_hand(oled, CENTER_X, CENTER_Y, 20, second_angle)

    # 中心点
    oled.pixel(CENTER_X, CENTER_Y, 1)
    oled.pixel(CENTER_X + 1, CENTER_Y, 1)
    oled.pixel(CENTER_X, CENTER_Y + 1, 1)
    oled.pixel(CENTER_X + 1, CENTER_Y + 1, 1)


def draw_environment_text(oled, temperature, humidity, pressure):
    text_x = 68
    oled.text("{:.1f}C".format(temperature), text_x, 4)
    oled.text("{:.1f}%".format(humidity), text_x, 24)
    oled.text("{:.0f}".format(pressure), text_x, 44)
    oled.text("hPa", text_x + 32, 54)


# === Wi-Fi / NTP ===

def connect_wifi(oled, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

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


# === メイン ===

def main():
    i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    bme = bme280.BME280(i2c=i2c)

    ip = connect_wifi(oled)
    if ip is None:
        print("WiFi failed. Rebooting in 5s...")
        time.sleep(5)
        import machine
        machine.reset()

    sync_time()

    # センサー初期値
    temperature, humidity, pressure = 0.0, 0.0, 0.0
    last_sensor_read = 0

    while True:
        now = time.time()

        # センサーは2秒ごとに読む
        if now - last_sensor_read >= 2:
            try:
                values = bme.values
                temperature = float(values[0].replace("C", "").strip())
                humidity = float(values[2].replace("%", "").strip())
                pressure = float(values[1].replace("hPa", "").strip())
            except (ValueError, IndexError, OSError):
                pass
            last_sensor_read = now

        # 現在時刻（JST）
        current_time = time.localtime(now + TZ_OFFSET)

        # 描画
        oled.fill(0)
        draw_environment_rings(oled, temperature, humidity, pressure)
        draw_clock_face(oled, current_time)
        draw_environment_text(oled, temperature, humidity, pressure)
        oled.show()

        time.sleep(0.5)


main()
