# This code is from the Pimoroni Motor 2040 example code

import gc
import time
from motor import Motor, motor2040
from encoder import Encoder, MMME_CPR
from pimoroni import Button, PID, REVERSED_DIR

"""
A demonstration of driving all four of Motor 2040's motor outputs through a
sequence of velocities, with the help of their attached encoders and PID control.

Press "Boot" to exit the program.
"""

GEAR_RATIO = 50                         # The gear ratio of the motors
OTHER_GEAR_RATIO = 298                  # The gear ratio of the problem motor
COUNTS_PER_REV = MMME_CPR * GEAR_RATIO  # The counts per revolution of each motor's output shaft
OTHER_COUNTS_PER_REV = MMME_CPR * OTHER_GEAR_RATIO  # The counts per revolution of each motor's output shaft

SPEED_SCALE = 5.4                       # The scaling to apply to each motor's speed to match its real-world speed
OTHER_SPEED_SCALE = SPEED_SCALE * (GEAR_RATIO / OTHER_GEAR_RATIO)

UPDATES = 100                           # How many times to update the motor per second
UPDATE_RATE = 1 / UPDATES
TIME_FOR_EACH_MOVE = 2                  # The time to travel between each value
UPDATES_PER_MOVE = TIME_FOR_EACH_MOVE * UPDATES
PRINT_DIVIDER = 4                       # How many of the updates should be printed (i.e. 2 would be every other update)

# PID values
VEL_KP = 30.0                           # Velocity proportional (P) gain
VEL_KI = 0.0                            # Velocity integral (I) gain
VEL_KD = 0.4                            # Velocity derivative (D) gain


# Free up hardware resources ahead of creating a new Encoder
gc.collect()

# Create a list of motors with a given speed scale
motors = [Motor(motor2040.MOTOR_A, speed_scale=OTHER_SPEED_SCALE),
          Motor(motor2040.MOTOR_B, speed_scale=SPEED_SCALE),
          Motor(motor2040.MOTOR_C, speed_scale=SPEED_SCALE),
          Motor(motor2040.MOTOR_D, speed_scale=SPEED_SCALE)]

# Create a list of encoders, using PIO 0, with the given counts per revolution
ENCODER_NAMES = ["RR", "RL", "FL", "FR"]
encoders = [Encoder(0, 0, motor2040.ENCODER_A, counts_per_rev=OTHER_COUNTS_PER_REV, count_microsteps=True),
            Encoder(0, 1, motor2040.ENCODER_B, counts_per_rev=COUNTS_PER_REV, count_microsteps=True),
            Encoder(0, 2, motor2040.ENCODER_C, counts_per_rev=COUNTS_PER_REV, count_microsteps=True),
            Encoder(0, 3, motor2040.ENCODER_D, counts_per_rev=COUNTS_PER_REV, count_microsteps=True)]

# Wheel friendly names
FL = 2
FR = 3
RL = 1
RR = 0

# Reverse the direction of the B and D motors and encoders
motors[FL].direction(REVERSED_DIR)
motors[RL].direction(REVERSED_DIR)
encoders[FL].direction(REVERSED_DIR)
encoders[RL].direction(REVERSED_DIR)
encoders[RR].direction(REVERSED_DIR)

# Create the user button
user_sw = Button(motor2040.USER_SW)

# Create PID objects for position control
vel_pids = [PID(VEL_KP, VEL_KI, VEL_KD, UPDATE_RATE) for i in range(motor2040.NUM_MOTORS)]

# Enable the motor to get started
for m in motors:
    m.enable()


update = 0
print_count = 0


# Helper functions for driving in common directions
def drive_forward(speed):
    vel_pids[FL].setpoint = speed
    vel_pids[FR].setpoint = speed
    vel_pids[RL].setpoint = speed
    vel_pids[RR].setpoint = speed


def turn_right(speed):
    vel_pids[FL].setpoint = speed
    vel_pids[FR].setpoint = -speed
    vel_pids[RL].setpoint = speed
    vel_pids[RR].setpoint = -speed


def strafe_right(speed):
    vel_pids[FL].setpoint = speed
    vel_pids[FR].setpoint = -speed
    vel_pids[RL].setpoint = -speed
    vel_pids[RR].setpoint = speed


def stop():
    vel_pids[FL].setpoint = 0
    vel_pids[FR].setpoint = 0
    vel_pids[RL].setpoint = 0
    vel_pids[RR].setpoint = 0


sequence = 0

captures = [None] * motor2040.NUM_MOTORS

# Continually move the motor until the user button is pressed
while user_sw.raw() is not True:

    # Capture the state of all the encoders
    for i in range(motor2040.NUM_MOTORS):
        captures[i] = encoders[i].capture()

    # Calculate how far along this movement to be
    percent_along = min(update / UPDATES_PER_MOVE, 1.0)

    for i in range(motor2040.NUM_MOTORS):
        # Calculate the acceleration to apply to the motor to move it closer to the velocity setpoint
        accel = vel_pids[i].calculate(captures[i].revolutions_per_second)

        # Accelerate or decelerate the motor
        motors[i].speed(motors[i].speed() + (accel * UPDATE_RATE))

    # Print out the current motor values, but only on every multiple
    if print_count == 0:
        for i in range(len(motors)):
            print(ENCODER_NAMES[i], "=", captures[i].revolutions_per_second, end=", ")
        print()

    # Increment the print count, and wrap it
    print_count = (print_count + 1) % PRINT_DIVIDER

    update += 1     # Move along in time

    # Have we reached the end of this movement?
    if update >= UPDATES_PER_MOVE:
        update = 0  # Reset the counter

        # Move on to the next part of the sequence
        sequence += 1

        # Loop the sequence back around
        if sequence >= 7:
            sequence = 0

    # Set the motor speeds, based on the sequence
    if sequence == 0:
        drive_forward(0.9)
    elif sequence == 1:
        drive_forward(-0.9)
    elif sequence == 2:
        turn_right(0.9)
    elif sequence == 3:
        turn_right(-0.0)
    elif sequence == 4:
        strafe_right(0.9)
    elif sequence == 5:
        strafe_right(-0.9)
    elif sequence == 6:
        stop()

    time.sleep(UPDATE_RATE)

# Stop all the motors
for m in motors:
    m.disable()