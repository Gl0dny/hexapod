from icm20948 import ICM20948

class Imu:
    """Interface for interacting with the ICM20948 IMU sensor, providing access to acceleration, gyroscope, magnetometer, and temperature data.

    ### Data Interpretation

    - Accel: Acceleration values along the X, Y, and Z axes in units of g (gravity).
    - (`get_acceleration`)
      - **X**: 00.01 g
      - **Y**: 00.01 g
      - **Z**: 01.01 g  
      *Interpretation*: The device experiences negligible acceleration on the X and Y axes and approximately 1 g on the Z-axis, indicating it is likely stationary and aligned with the gravitational force.

    - Gyro: Angular velocity around the X, Y, and Z axes in degrees per second.
    - (`get_gyroscope`)
      - **X**: 00.46 °/s
      - **Y**: 01.14 °/s
      - **Z**: -0.35 °/s  
      *Interpretation*: The device has minimal angular velocity around the X and Y axes, suggesting slight rotation. The negative value on the Z-axis indicates rotation in the opposite direction.
    
    - Mag: Magnetic field strength along the X, Y, and Z axes in microteslas (µT).
    - (`get_magnetometer`)
      - **X**: -4.95 µT
      - **Y**: -6.30 µT
      - **Z**: 103.95 µT  
      *Interpretation*: These values represent the magnetic field strength in microteslas along each axis. The Z-axis has a significantly higher value, which may indicate the device's orientation relative to the Earth's magnetic field.
    
    - Temperature: The current temperature measured by the IMU sensor in degrees Celsius.
      - (`get_temperature`)*:
      - **33.11 °C**  
      - Interpretation: The sensor's temperature is within a typical operating range, ensuring accurate measurements.
    """
        
    def __init__(self):
        """Initialize the Imu class by creating an instance of ICM20948."""
        self.imu = ICM20948()

    def get_acceleration(self):
        """Retrieve acceleration data along the x, y, and z axes.
        
        Returns:
            tuple: A tuple containing acceleration values (ax, ay, az).
        """
        ax, ay, az, gx, gy, gz = self.imu.read_accelerometer_gyro_data()
        return ax, ay, az

    def get_gyroscope(self):
        """Retrieve gyroscopic data along the x, y, and z axes.
        
        Returns:
            tuple: A tuple containing gyroscopic values (gx, gy, gz).
        """
        ax, ay, az, gx, gy, gz = self.imu.read_accelerometer_gyro_data()
        return gx, gy, gz

    def get_magnetometer(self):
        """Retrieve magnetometer data along the x, y, and z axes.
        
        Returns:
            tuple: A tuple containing magnetometer values (x, y, z).
        """
        return self.imu.read_magnetometer_data()

    def get_temperature(self):
        """Retrieve the temperature reading from the IMU sensor.
        
        Returns:
            float: The temperature value.
        """
        return self.imu.read_temperature()


if __name__ == "__main__":
    imu = Imu()
    ax, ay, az = imu.get_acceleration()
    gx, gy, gz = imu.get_gyroscope()
    mag_x, mag_y, mag_z = imu.get_magnetometer()
    temp = imu.get_temperature()

    print(f"""
Accel: {ax:05.2f} {ay:05.2f} {az:05.2f}
Gyro:  {gx:05.2f} {gy:05.2f} {gz:05.2f}
Mag:   {mag_x:05.2f} {mag_y:05.2f} {mag_z:05.2f}
Temp:  {temp:05.2f}""")
