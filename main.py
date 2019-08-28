import RPi.GPIO as GPIO
import subprocess
import time
from w1thermsensor import W1ThermSensor

import listener


class Sensor:
    def __init__(self, pin, nameGET):
        self.pin = pin
        self.nameGET = nameGET
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self):
        return GPIO.input(self.pin)

    def getRequest(self):
        print("get request send:{}".format(self.nameGET))
        subprocess.call([
            "curl", "-m", "1", "-X", "GET",
            "http://192.168.42.42:14999/{}".format(self.nameGET)
        ])

    def check_run(self):
        if self.read() and game_state[self.nameGET] == False:
            print(game_state)
            game_state[self.nameGET] = True
            print(game_state)
            self.getRequest()


def check_run_temperature(sensor):
    if sensor.get_temperature() > (start_temperature + 2):
        subprocess.call([
            "curl", "-m", "1", "-X", "GET",
            "http://192.168.42.42:14999/temperature"
        ])
        GPIO.output(bird, True)
        GPIO.output(moine, True)


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
    moine = None  #need change !!!!!!
    GPIO.setup(bird, GPIO.OUT)
    GPIO.setup(moine, GPIO.OUT)


def wait_start():
    if listener.server_program() == "start":
        print("c'est parti !")
        subprocess.call(
            ["curl", "-X", "GET", "http://192.168.42.42:14999/start"])
        time.sleep(5)
        subprocess.call(
            ["curl", "-X", "GET", "http://192.168.42.42:14999/machine"])


def main():
    init()
    wait_start()
    while (1):
        atelier.check_run()
        caveau.check_run()
        serre.check_run()
        check_run_temperature(sensor_temperature)


if __name__ == "__main__":
    main()