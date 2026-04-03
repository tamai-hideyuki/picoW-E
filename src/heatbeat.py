from machine import Pin
import time

led = Pin('LED', Pin.OUT)

def heatbeat(bpm=70):
    cycle = 60 / bpm

    led.on()
    time.sleep(0.05)
    led.off()
    time.sleep(0.08)

    led.on()
    time.sleep(0.05)
    led.off()

    time.sleep(cycle - 0.23)

while True:
    heatbeat(bpm=70)

