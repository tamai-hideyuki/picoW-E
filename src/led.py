from machine import Pin
import time

led = Pin("LED", Pin.OUT)

led.on()
time.sleep(2)
led.off()
