#!/usr/bin/env python3
from icm20948 import ICM20948

class Imu:
    def __init__(self):
        self._imu = ICM20948()

    def read_temperature(self):
        return self._imu.read_temperature()

if __name__ == "__main__":
    imu = Imu()
    temperature = imu.read_temperature()
    print(f"Temperature: {temperature} °C")