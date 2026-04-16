import bme280


class Sensor:
    def __init__(self, i2c):
        self.bme = bme280.BME280(i2c=i2c)

    def read(self):
        try:
            values = self.bme.values
            temp = float(values[0].replace("C", "").strip())
            pres = float(values[1].replace("hPa", "").strip())
            humi = float(values[2].replace("%", "").strip())
            return temp, humi, pres
        except (ValueError, IndexError, OSError):
            return None
