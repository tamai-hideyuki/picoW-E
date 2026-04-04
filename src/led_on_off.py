import ssd1306
import network
import socket
import time
from machine import Pin, I2C

led = Pin("LED", Pin.OUT)

SSID = "Wi-Fi名"
PASSWORD = "パスワード"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    time.sleep(1)

ip = wlan.ifconfig()[0]

time.sleep(2)

i2c = I2C(0,sda=Pin(0), scl=Pin(1))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)
oled.text("Connected!", 0, 0)
oled.text(ip, 0, 16)
oled.show()

html = """\
HTTP/1.0 200 OK
Content-Type: text/html

<html>
<body>
    <h1>LED Control</h1>
    <button onclick="fetch('/led/on')">ON</button>
    <button onclick="fetch('/led/off')">OFF</button>
</body>
</html>
"""

addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

oled.fill(0)
oled.text("Server ready", 0, 0)
oled.text(ip, 0, 16)
oled.show()

print("サーバー起動:", ip)

while True:
    conn, addr = s.accept()
    request = conn.recv(1024).decode()

    if "/led/on" in request:
        led.on()
    elif "/led/off" in request:
        led.off()

    conn.sendall(html)
    conn.close()
