#!/usr/bin/env python3

__author__ = 'anton'

import evdev
import ev3dev.auto as ev3
import threading
import time

#Helpers
def clamp(n, range):
    """
    Given a number and a range, return the number, or the extreme it is closest to.

    :param n: number
    :return: number
    """
    minn, maxn = range
    return max(min(maxn, n), minn)


def scale(val, src, dst):
    """
    Scale the given value from the scale of src to the scale of dst.

    val: float or int
    src: tuple
    dst: tuple

    example: print scale(99, (0.0, 99.0), (-1.0, +1.0))
    """
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

def scalestick(value):
    return scale(value,(0,255),(-700,700))

print("Finding ps3 controller...")
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
for device in devices:
    if device.name == 'PLAYSTATION(R)3 Controller':
        ps3dev = device.fn

gamepad = evdev.InputDevice(ps3dev)



side_speed = 0
turn_speed = 0
fwd_speed = 0
triangle_pressed_time = 0
medium_motor_speed = -500
shooting = 0
running = True

class ShooterThread(threading.Thread):
    def __init__(self):
        self.medium_motor = ev3.MediumMotor(ev3.OUTPUT_A)
        self.touch_sensor = ev3.TouchSensor(ev3.INPUT_1)
        threading.Thread.__init__(self)

    def run(self):
        print("Shooter running!")
        self.medium_motor.run_forever(speed_sp=300)
        while not self.touch_sensor.is_pressed:
            time.sleep(0.1)
        self.medium_motor.run_to_rel_pos(position_sp=200, speed_sp=600)
        while running:
            if shooting:
                self.medium_motor.run_forever(speed_sp=700)
                while not self.touch_sensor.is_pressed:
                    time.sleep(0.1)
                self.medium_motor.run_to_rel_pos(position_sp=200, speed_sp=600)
            else:
                self.medium_motor.run_forever(speed_sp=medium_motor_speed)

        self.medium_motor.stop()

class MotorThread(threading.Thread):
    def __init__(self):
        self.left_motor = ev3.LargeMotor(ev3.OUTPUT_B)
        self.right_motor = ev3.LargeMotor(ev3.OUTPUT_C)
        threading.Thread.__init__(self)

    def run(self):
        print("Engines running!")
        while running:
            self.left_motor.run_forever(speed_sp=clamp(fwd_speed + side_speed//2, (-700,700)))
            self.right_motor.run_forever(speed_sp=clamp(fwd_speed - side_speed//2, (-700,700)))

        self.left_motor.stop()
        self.right_motor.stop()


if __name__ == "__main__":
    motor_thread = MotorThread()
    motor_thread.setDaemon(True)
    motor_thread.start()
    shooter_thread = ShooterThread()
    shooter_thread.setDaemon(True)
    shooter_thread.start()

    for event in gamepad.read_loop(): #this loops infinitely
        if event.type == 3: #A stick is moved

            if event.code == 2: #X axis on right stick
                side_speed = scalestick(event.value)

            if event.code == 5: #Y axis on right stick
                fwd_speed = scalestick(event.value)


        if event.type == 1:
            if event.code == 300:
                if event.value == 1:
                    triangle_pressed_time = time.time()
                if event.value == 0 and time.time() > triangle_pressed_time + 1:
                    print("Triangle button is pressed. Break.")
                    running = False
                    time.sleep(0.5) # Wait for the motor thread to finish
                    break
            elif event.code == 302:
                print("X button is pressed. Shoot!")
                shooting = event.value

