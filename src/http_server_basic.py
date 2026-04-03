import ssd1306
import network
import socket
import time
from machine import Pin, I2C

SSID = "Wi-Fi名"
PASSWORD = "パスワード"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    time.sleep(1)

ip = wlan.ifconfig()[0]

time.sleep(2)

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)
oled.text("Connecting...", 0, 0)
oled.show()


oled.fill(0)
oled.text("Connected!", 0, 0)
oled.text(ip, 0, 16)
oled.show()

html = f"""\
HTTP/1.0 200 OK
Content-Type: text/html

<html>
<style>
    body {
        background-color: black;
        color: white;
    }
</style>
<body>
    <h1>Hello!</h1>
    <h2>Hello!</h2>
    <h3>Hello!</h3>
    <h4>Hello!</h4>
    <h5>Hello!</h5>
    <h6>Hello!</h6>
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
    conn.recv(1024)
    conn.sendall(html)
    conn.close()
