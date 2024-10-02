"""
Pololu Maestro servo controller board library
"""
import serial

class MaestroUART(object):
	def __init__(self, device='/dev/ttyS0', baudrate=9600):
		"""Open the given serial port and do any setup for the serial port.

		Args:
			device: The name of the serial port that the Maestro is connected to.
				Default is '/dev/ttyS0'.
				Examples: "/dev/ttyAMA0" for Raspberry Pi 2, "/dev/ttyS0" for 
				Raspberry Pi 3.
			baudrate: Default is 9600.
		"""
		self.ser = serial.Serial(device)
		self.ser.baudrate = baudrate
		self.ser.bytesize = serial.EIGHTBITS
		self.ser.parity = serial.PARITY_NONE
		self.ser.stopbits = serial.STOPBITS_ONE
		self.ser.xonxoff = False
		self.ser.timeout = 0 # makes the read non-blocking

	def get_error(self):
		"""Check if there was an error.

		Returns:
			>0: error, see the Maestro manual for the error values
			0: no error, or error getting the position, check the connections,
			could also be low power
		"""
		command = bytes([0xAA, 0x0C, 0xA1 & 0x7F])

		self.ser.write(command)

		data = [b'\x00', b'\x00']
		n = 0
		while n != 2:
			data[n] = self.ser.read(1)
			if not data[n]: continue
			n = n + 1

		return int.from_bytes(data[0], byteorder='big') & 0x7F + (int.from_bytes(data[1], byteorder='big') & 0x7F) << 7

	def get_position(self, channel):
		"""Gets the position of a servo from a Maestro channel.
	
		Args:
			channel: The channel for the servo motor (0, 1, ...).

		Returns:
			>0: the servo position in quarter-microseconds
			0: error getting the position, check the connections, could also be
			low power
		""" 
		command = bytes([0xAA, 0x0C, 0x90 & 0x7F, channel])

		self.ser.write(command)

		data = [b'\x00', b'\x00']
		n = 0
		while n != 2:
			data[n] = self.ser.read(1)
			if not data[n]: continue
			n = n + 1

		return int.from_bytes(data[0], byteorder='big') + 256 * int.from_bytes(data[1], byteorder='big')

	def set_speed(self, channel, speed):
		"""Sets the speed of a Maestro channel.

		Args:
			channel: The channel for the servo motor (0, 1, ...).
		 	speed: The speed you want the motor to move at. The units of 
				'speed' are in units of (0.25us/10ms). A speed of 0 means 
				unlimited.

		Example (speed is 32):
		Let's say the distance from your current position to the target 
		is 1008us and you want to take 1.25 seconds (1250ms) to get there. 
		The required speed is (1008us/1250ms) = 0.8064us/ms.
		Converting to units of (0.25us/10ms), 
		0.8064us/ms / (0.25us/10ms) = 32.256.
		So we'll use 32 for the speed.

		Example (speed is 140, from the Maestro manual):
		Let's say we set the speed to 140. That is a speed of 
		3.5us/ms (140 * 0.25us/10ms = 3.5us/ms). If your target is such that 
		you're going from 1000us to 1350us, then it will take 100ms.

		Returns:
			none
		"""
		command = bytes([0xAA, 0x0C, 0x87 & 0x7F, channel, speed & 0x7F, (speed >> 7) & 0x7F])
		self.ser.write(command)

	def set_acceleration(self, channel, accel):
		"""Sets the acceleration of a Maestro channel. Note that once you set
		the acceleration, it will still be in effect for all your movements
		of that servo motor until you change it to something else.

		Args:
			channel: The channel for the servo motor (0, 1, ...).
			accel: The rate at which you want the motor to accelerate in
				the range of 0 to 255. 0 means there's no acceleration limit.
				The value is in units of (0.25 us)/(10 ms)/(80 ms).

		Example (acceleration is ):
		Let's say our motor is currently not moving and we're setting our 
		speed to 32, meaning 0.8064us/ms (see the example for set_speed()).
		Let's say we want to get up to that speed in 0.5 seconds. 
		Think of 0.8064us/ms as you would 0.8064m/ms (m for meters) if you 
		find the 'us' confusing.
		Step 1. Find the acceleration in units of us/ms/ms:
		accel = (Vfinal - Vinitial) / time, V means velocity or speed
		Vfinal = 0.8064us/ms
		Vinitial = 0us/ms (the motor was not moving to begin with)
		time = 0.5 seconds = 500ms
		Therefore:
		accel = (0.8064us/ms - 0us/ms) / 500ms = 0.0016128us/ms/ms
		Step 2. Convert to units of (0.25 us)/(10 ms)/(80 ms):
		0.0016128us/ms/ms / [(0.25 us)/(10 ms)/(80 ms)] = 
		0.0016128us/ms/ms / 0.0003125us/ms/ms = 5.16096
		So we'll set the acceleration to 5.

		Example (acceleration is 4, from the Maestro manual):
		A value of 4 means that you want the speed of the servo to change
		by a maximum of 1250us/s every second.
		4 x 0.25us / 10ms / 80ms = 0.00125us/ms/ms,
		which is 1250us/s/s.

		Returns:
			none
		"""
		command = bytes([0xAA, 0x0C, 0x89 & 0x7F, channel, accel & 0x7F, (accel >> 7) & 0x7F])
		self.ser.write(command)

	def set_target(self, channel, target):
		"""Sets the target of a Maestro channel. 

		Args:
			channel: The channel for the servo motor (0, 1, ...).
			target: Where you want the servo to move to in quarter-microseconds.
				Allowing quarter-microseconds gives you more resolution to work
				with.
				Example: If you want to move it to 2000us then pass 
				8000us (4 x 2000us).

		Returns:
			none
		"""
		command = bytes([0xAA, 0x0C, 0x84 & 0x7F, channel, target & 0x7F, (target >> 7) & 0x7F])
		self.ser.write(command)

	def close(self):
		"""
		Close the serial port.

		Args:
			none

		Returns:
			none
		"""
		self.ser.close();

if __name__ == '__main__':
	# min_pos and max_pos are the minimum and maxium positions for the servos
	# in quarter-microseconds. The defaults are 992*4 and 2000*4. See the Maestro
	# manual for how to change these values.
	# Allowing quarter-microseconds gives you more resolution to work with.
	# e.g. If you want a maximum of 2000us then use 8000us (4 x 2000us).

	min_pos = 992*4
	max_pos = 2000*4

	mu = MaestroUART('/dev/ttyS0', 9600)
	channel = 0

	error = mu.get_error()
	if error:
		print(error)

	accel = 5
	mu.set_acceleration(channel, accel)

	speed = 32
	mu.set_speed(channel, speed)

	position = mu.get_position(channel)

	print('Position is: %d quarter-microseconds' % position)

	if position < min_pos+((max_pos - min_pos)/2): # if less than halfway
		target = max_pos
	else:
		target = min_pos

	print('Moving to: %d quarter-microseconds' % target)

	mu.set_target(channel, target)

	mu.close()
