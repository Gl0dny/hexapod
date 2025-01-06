"""
Pololu Maestro servo controller board library

### Pololu Protocol

This protocol is compatible with the serial protocol used by our other serial motor and servo controllers. 
As such, you can daisy-chain a Maestro on a single serial line along with our other serial controllers (including additional Maestros) and, using this protocol, 
send commands specifically to the desired Maestro without confusing the other devices on the line.

To use the Pololu protocol, you transmit 0xAA (170 in decimal) as the first (command) byte, followed by a Device Number data byte. 
The default Device Number for the Maestro is **12**, but this is a configuration parameter you can change. 
Any Maestro on the line whose device number matches the specified device number accepts the command that follows; all other Pololu devices ignore the command. 
The remaining bytes in the command packet are the same as the compact protocol command packet you would send, with one key difference: 
the compact protocol command byte is now a data byte for the command 0xAA and hence **must have its most significant bit cleared**. -> & 0x7F
Therefore, the command packet is:

**0xAA, device number byte, command byte with MSB cleared, any necessary data bytes**

For example, if we want to set the target of servo 0 to 1500 µs for a Maestro with device number 12, we could send the following byte sequence:

in hex: **0xAA, 0x0C, 0x04, 0x00, 0x70, 0x2E**  
in decimal: **170, 12, 4, 0, 112, 46**

Note that 0x04 is the command 0x84 with its most significant bit cleared.
"""
import serial
import time
from typing import Optional

COMMAND_START: int = 0xAA
DEFAULT_DEVICE_NUMBER: int = 0x0C
COMMAND_GET_ERROR: int = 0xA1 & 0x7F
COMMAND_GET_POSITION: int = 0x90 & 0x7F
COMMAND_SET_SPEED: int = 0x87 & 0x7F
COMMAND_SET_ACCELERATION: int = 0x89 & 0x7F
COMMAND_SET_TARGET: int = 0x84 & 0x7F
COMMAND_GO_HOME: int = 0x22 & 0x7F
COMMAND_GET_MOVING_STATE: int = 0x93 & 0x7F
COMMAND_SET_MULTIPLE_TARGETS: int = 0x1F

class MaestroUART(object):
	def __init__(self, device: str = '/dev/ttyS0', baudrate: int = 9600) -> None:
		"""Open the given serial port and do any setup for the serial port.

		Args:
			device: The name of the serial port that the Maestro is connected to.
				Default is '/dev/ttyS0'.
				Examples: "/dev/ttyAMA0" for Raspberry Pi 2, "/dev/ttyS0" for 
				Raspberry Pi 3.
			baudrate: Default is 9600.
		"""
		self.ser: serial.Serial = serial.Serial(device)
		self.ser.baudrate = baudrate
		self.ser.bytesize = serial.EIGHTBITS
		self.ser.parity = serial.PARITY_NONE
		self.ser.stopbits = serial.STOPBITS_ONE
		self.ser.xonxoff = False
		self.ser.timeout = 0 # makes the read non-blocking

	def get_error(self) -> int:
		"""Check if there was an error and print the corresponding error messages.

		• Serial signal error (bit 0)
			A hardware-level error that occurs when a byte’s stop bit is not detected at the expected
			place. This can occur if you are communicating at a baud rate that differs from the Maestro’s
			baud rate.
		• Serial overrun error (bit 1)
			A hardware-level error that occurs when the UART’s internal buffer fills up. This should not
			occur during normal operation.
		• Serial buffer full (bit 2)
			A firmware-level error that occurs when the firmware’s buffer for bytes received on the RX
			line is full and a byte from RX has been lost as a result. This error should not occur during
			normal operation.
		• Serial CRC error (bit 3)
			This error occurs when the Maestro is running in CRC-enabled mode and the cyclic
			redundancy check (CRC) byte at the end of the command packet does not match what the
			Maestro has computed as that packet’s CRC.
		• Serial protocol error (bit 4)
			This error occurs when the Maestro receives an incorrectly formatted or illogal
			command packet.
		• Serial timeout (bit 5)
			When the serial timeout is enabled, this error occurs whenever the timeout period has
			elapsed without the Maestro receiving any valid serial commands.
		• Script stack error (bit 6)
			This error occurs when a bug in the user script has caused the stack to overflow or underflow.
		• Script call stack error (bit 7)
			This error occurs when a bug in the user script has caused the call stack to overflow or
			underflow.
		• Script program counter error (bit 8)
			This error occurs when a bug in the user script has caused the program counter to go out
			of bounds.

		Returns:
			>0: error, see the Maestro manual for the error values
			0: no error, or error getting the position, check the connections, could also be low power
		"""
		command = bytes([COMMAND_START, DEFAULT_DEVICE_NUMBER, COMMAND_GET_ERROR])

		self.ser.write(command)

		data = [b'\x00', b'\x00']
		n = 0
		while n != 2:
			data[n] = self.ser.read(1)
			if data[n] == b'': continue
			n = n + 1

		error_code = int.from_bytes(data[0], byteorder='big') + (int.from_bytes(data[1], byteorder='big') << 8)

		if error_code != 0:
			print("Error detected with code:", error_code)
			if error_code & (1 << 0):
				print("Serial signal error: Stop bit not detected at the expected place.")
			if error_code & (1 << 1):
				print("Serial overrun error: UART's internal buffer filled up.")
			if error_code & (1 << 2):
				print("Serial buffer full: Firmware buffer for received bytes is full.")
			if error_code & (1 << 3):
				print("Serial CRC error: CRC byte does not match the computed CRC.")
			if error_code & (1 << 4):
				print("Serial protocol error: Incorrectly formatted or nonsensical command packet.")
			if error_code & (1 << 5):
				print("Serial timeout: Timeout period elapsed without receiving valid serial commands.")
			if error_code & (1 << 6):
				print("Script stack error: Stack overflow or underflow.")
			if error_code & (1 << 7):
				print("Script call stack error: Call stack overflow or underflow.")
			if error_code & (1 << 8):
				print("Script program counter error: Program counter went out of bounds.")
				
		return error_code

	def get_position(self, channel: int) -> int:
		"""Gets the position of a servo from a Maestro channel.
	
		Args:
			channel: The channel for the servo motor (0, 1, ...).

		Returns:
			>0: the servo position in quarter-microseconds
			0: error getting the position, check the connections, could also be
			low power
		""" 
		self.ser.reset_input_buffer()
		command = bytes([COMMAND_START, DEFAULT_DEVICE_NUMBER, COMMAND_GET_POSITION, channel])

		self.ser.write(command)

		data = [b'\x00', b'\x00']
		n = 0
		while n != 2:
			data[n] = self.ser.read(1)
			if data[n] == b'': continue
			n = n + 1

		return int.from_bytes(data[0], byteorder='big') + (int.from_bytes(data[1], byteorder='big') << 8)

	def set_speed(self, channel: int, speed: int) -> None:
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
		command = bytes([COMMAND_START, DEFAULT_DEVICE_NUMBER, COMMAND_SET_SPEED, channel, speed & 0x7F, (speed >> 7) & 0x7F])
		self.ser.write(command)

	def set_acceleration(self, channel: int, accel: int) -> None:
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
		command = bytes([COMMAND_START, DEFAULT_DEVICE_NUMBER, COMMAND_SET_ACCELERATION, channel, accel & 0x7F, (accel >> 7) & 0x7F])
		self.ser.write(command)

	def set_target(self, channel: int, target: int) -> None:
		"""Sets the target of a Maestro channel. 

		Args:
			channel: The channel for the servo motor (0, 1, ...).
			target: Where you want the servo to move to in quarter-microseconds.
				Allowing quarter-microseconds gives you more resolution to work
				with.
				Example: If you want to move it to 2000us then pass 
				8000us (4 x 2000us).

				A target value of 0 tells the Maestro to stop sending pulses to the servo.
				
		Returns:
			none
		"""
		command = bytes([COMMAND_START, DEFAULT_DEVICE_NUMBER, COMMAND_SET_TARGET, channel, target & 0x7F, (target >> 7) & 0x7F])
		self.ser.write(command)

	def set_multiple_targets(self, targets: list[tuple[int, int]]) -> None:
		"""
		This command simultaneously sets the targets for a contiguous block of channels.
		**Note:** Targets must be provided in sequential order by channel number.

		The first byte specifies how many channels are in the contiguous block; this is the 
		number of target values you will need to send. The second byte specifies the lowest 
		channel number in the block. The subsequent bytes contain the target values for each 
		of the channels, in order by channel number, in the same format as the Set Target 
		command above.

		For example, to set channel 3 to 0 (off) and channel 4 to 6000 (neutral), you would 
		send the following bytes:
		0x9F, 0x02, 0x03, 0x00, 0x00, 0x70, 0x2E

		The Set Multiple Targets command allows high-speed updates to your Maestro, which 
		is especially useful when controlling a large number of servos in a chained configuration. 
		For example, using the Pololu protocol at 115.2 kbps, sending the Set Multiple Targets 
		command lets you set the targets of 24 servos in 4.6 ms, while sending 24 individual Set 
		Target commands would take 12.5 ms.

		Args:
			targets (list of tuples): Each tuple contains (channel, target).
				Example: [(3, 0), (4, 6000)]
		"""
		# Check if channels are sequential
		channels = [channel for channel, _ in targets]
		if channels != list(range(min(channels), min(channels) + len(channels))):
			raise ValueError("Channels are not sequential.")
		num_targets = len(targets)
		first_channel = targets[0][0]
		command = bytes([COMMAND_START, DEFAULT_DEVICE_NUMBER, COMMAND_SET_MULTIPLE_TARGETS, num_targets, first_channel])
		for _, target in targets:
			command += bytes([target & 0x7F, (target >> 7) & 0x7F])
		self.ser.write(command)

	def go_home(self) -> None:
		"""
		Sends a command to set all servos and outputs to their home positions.
		For servos marked "Ignore", the position will remain unchanged.
		For servos marked “Off”, if you execute a Set Target command immediately after
		Go Home, it will appear that the servo is not obeying speed and acceleration limits. In
		fact, as soon as the servo is turned off, the Maestro has no way of knowing where it is,
		so it will immediately move to any new target. Subsequent target commands will function
		normally

		Args:
			none

		Returns:
			none
		"""

		command = bytes([COMMAND_START, DEFAULT_DEVICE_NUMBER, COMMAND_GO_HOME])
		self.ser.write(command)

	def get_moving_state(self) -> Optional[int]:
		"""
		Checks if any servos are still moving.
		This command is used to determine whether the servo outputs have reached 
		their targets or are still changing and will return 1 as long as there is 
		at least one servo that is limited by a speed or acceleration setting still moving.
		Using this command together with the Set Target command, you can initiate several 
		servo movements and wait for all the movements to finish before moving on to the 
		next step of your program.

		Args:
			none

		Returns:
			Optional[int]: The moving state or None if no response is received.
			0x00: if no servos are moving
			0x01: if at least one servo is still moving
		"""
		self.ser.reset_input_buffer()
		command = bytes([COMMAND_START, DEFAULT_DEVICE_NUMBER, COMMAND_GET_MOVING_STATE])
		self.ser.write(command)

		# Read a single byte response indicating the moving state
		response = self.ser.read(1)
		if response == b'':
			return None
		return ord(response)

	def close(self) -> None:
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

	min_pos = 1100*4
	max_pos = 1800*4

	mu = MaestroUART('/dev/ttyS0', 9600)
	channel = 8

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

	
	first_iteration = True
	while True:
		moving_state = mu.get_moving_state()

		if first_iteration and moving_state is None:
			first_iteration = False
			time.sleep(0.1)
			continue

		if moving_state is not None:
			if moving_state == 0x00:
				print("All servos have stopped moving.")
				break
			else:
				print("Servos are still moving...")
		else:
			print("Failed to get the moving state.")
			break

		time.sleep(0.1)

	mu.go_home()
	print("Servos set to home positions.")

	mu.close()
