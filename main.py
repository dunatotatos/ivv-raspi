import RPi.GPIO as GPIO
import subprocess
import time
from w1thermsensor import W1ThermSensor
from w1thermsensor.errors import ResetValueError

import listener
import constant


class Sensor:
    def __init__(self, pin, name_get):
        self.pin = pin
        self.name_get = name_get
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self):
        return GPIO.input(self.pin)

    def get_request(self):
        print("get request send:{}".format(self.name_get))
        subprocess.call([
            "curl", "-m", "1", "-X", "GET", "{}{}".format(
                constant.url, self.name_get)
        ])

    def check_run(self):
        if self.read() and game_state[self.name_get] == False:
            print(game_state)
            game_state[self.name_get] = True
            print(game_state)
            self.get_request()


def check_run_temperature(sensor):
    def safe_get_temperature(sensor):
        """
        Try hard to return the reading of the temp sensor.

        This method tries to get the temperature from the sensor,
        and catches random exceptions due to bad communication.
        An exception is still raised if the problem of bad
        communication is persistent.

        Return
        ------
        int: temperature in Celcius

        Raise
        -----
        w1thermsensor.error.ResetValueError
            If the sensor is not reachable.

        """
        nb_exceptions = 0
        while True:
            try:
                current_temperature = sensor.get_temperature()
            except ResetValueError:
                print("Temperature sensor sent reset value. Ignoring.")
                nb_exceptions += 1
                if nb_exceptions >= 10:
                    raise
            else:
                return current_temperature
            time.sleep(0.1)

    current_temperature = safe_get_temperature(sensor)

    if current_temperature > (start_temperature + 2):
        GPIO.output(moine, True)
        subprocess.call([
            "curl", "-m", "1", "-X", "GET",
            "{}temperature".format(constant.url)
        ])
        time.sleep(61)
        GPIO.output(bird, True)
        time.sleep(50)
        while True:
            GPIO.output(bird, False)


def init():
    GPIO.setmode(GPIO.BCM)

    global atelier
    global caveau
    global serre
    global game_state
    global sensor_temperature
    sensor_temperature = W1ThermSensor()
    global start_temperature
    start_temperature = sensor_temperature.get_temperature()

    game_state = {"atelier": False, "caveau": False, "serre": False}
    atelier = Sensor(11, "atelier")
    caveau = Sensor(5, "caveau")
    serre = Sensor(9, "serre")

    global bird
    bird = 21
    global moine
    moine = 20
    GPIO.setup(bird, GPIO.OUT)
    GPIO.setup(moine, GPIO.OUT)


def wait_start():
    if listener.server_program() == "start":
        print("c'est parti !")
        subprocess.call(["curl", "-X", "GET", "{}start".format(constant.url)])
        time.sleep(5)
        subprocess.call(
            ["curl", "-X", "GET", "{}machine".format(constant.url)])


def main():
    try:
        init()
        wait_start()
        while (True):
            atelier.check_run()
            caveau.check_run()
            serre.check_run()
            check_run_temperature(sensor_temperature)
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
