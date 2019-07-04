import RPi.GPIO as GPIO
import subprocess
import time
from w1thermsensor import W1ThermSensor


class Sensor:
    def __init__(self, pin, nameGET):
        self.pin = pin
        self.nameGET = nameGET
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self):
        return GPIO.input(self.pin)

    def getRequest(self):
        print("get request send")
        subprocess.call([
            "curl", "-X", "GET",
            "http://192.168.42.42:14999/{}".format(self.nameGET)
        ])

    def check_run(self):
        if self.read():
            self.getRequest()


def check_run_temperature(sensor):
    if sensor.get_temperature() > 35:
        subprocess.call(
            ["curl", "-X", "GET", "http://192.168.42.42:14999/temperature"])


def init():
    GPIO.setmode(GPIO.BCM)

    global atelier
    global caveau
    global serre
    global sensor_temperature
    atelier = Sensor(10, "okok")
    caveau = Sensor(11, "okok")
    serre = Sensor(12, "okok")
    sensor_temperature = W1ThermSensor()


def main():
    init()
    while (1):
        atelier.check_run()
        caveau.check_run()
        serre.check_run()
        check_run_temperature(sensor_temperature)


if __name__ == "__main__":
    main()