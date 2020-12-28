import RPi.GPIO as GPIO
import subprocess
import time
import logging
import sys
from w1thermsensor import W1ThermSensor
from w1thermsensor.errors import ResetValueError

import listener
import constant

LOG = logging.getLogger(__name__)


class Sensor:
    """
    Interface with an electronic sensor connected to the baord.

    This class is used to check if a sensor is active or not, and send the
    associated request to Houdini.

    int pin: GPIO number where the positive wire of the sensor is connected
    str name_get: trailing part of the URL where an HTTP request is sent when
        the sensor is activated
    bool reverse: indicate if activated sensor makes GPIO.input() True
        (default) or False (reverse = True)

    """

    def __init__(self, pin, name_get, reverse=False):
        self.pin = pin
        self.name_get = name_get
        self.reverse = reverse
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self):
        """Return the status of the sensor as True or False."""
        return bool(GPIO.input(self.pin)) ^ self.reverse

    def get_request(self):
        """Send a signal to Houdini for this sensor."""
        LOG.debug("get request send: %s\n", self.name_get)
        subprocess.call([
            "curl", "-m", "1", "-X", "GET", "{}{}".format(
                constant.URL_DST, self.name_get)
        ])

    def check_run(self):
        """
        Cif the sensor is active, and send a request to Houdini.

        This method combines self.read and self.get_request in a simple
        one-shot method.

        """
        if self.read() and game_state[self.name_get] == False:
            LOG.debug("Activate %s sensor.\n", self.name_get)
            game_state[self.name_get] = True
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
                nb_exceptions += 1
                LOG.warning(
                    "Temperature sensor sent reset value %s times. Ignoring.",
                    nb_exceptions)
                if nb_exceptions >= 10:
                    LOG.error("Maximum number of hardware failures reached. Stopping...")
                    raise
            else:
                return current_temperature
            time.sleep(0.1)

    current_temperature = safe_get_temperature(sensor)
    LOG.debug("Current temperature: %s.", str(current_temperature))

    if current_temperature > (start_temperature + 2):
        GPIO.output(constant.MOINE_GPIO, True)
        subprocess.call([
            "curl", "-m", "1", "-X", "GET",
            "{}temperature".format(constant.URL_DST)
        ])
        time.sleep(61)
        GPIO.output(constant.BIRD_GPIO, True)
        time.sleep(50)
        while True:
            GPIO.output(constant.BIRD_GPIO, False)


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
    atelier = Sensor(constant.ATELIER_GPIO, "atelier")
    caveau = Sensor(constant.CAVEAU_GPIO, "caveau")
    serre = Sensor(constant.SERRE_GPIO, "serre")

    GPIO.setup(constant.BIRD_GPIO, GPIO.OUT)
    GPIO.setup(constant.MOINE_GPIO, GPIO.OUT)


def wait_start():
    if listener.server_program() == "start":
        LOG.info("C'est parti !")
        subprocess.call(
            ["curl", "-X", "GET", "{}start".format(constant.URL_DST)])
        time.sleep(5)
        subprocess.call(
            ["curl", "-X", "GET", "{}machine".format(constant.URL_DST)])


def main():
    LOG.info("Start service.")
    try:
        LOG.debug("Initializing.")
        init()
        LOG.debug("Wait for game start.")
        wait_start()
        LOG.debug("Game started.")
        while (True):
            LOG.debug("Check atelier.")
            atelier.check_run()
            LOG.debug("Check caveau.")
            caveau.check_run()
            LOG.debug("Check serre.")
            serre.check_run()
            LOG.debug("Check temperature.")
            check_run_temperature(sensor_temperature)
    finally:
        GPIO.cleanup()
        LOG.info("Stop service.")


if __name__ == "__main__":
    LOG.setLevel(logging.INFO)
    STDOUT_HANDLER = logging.StreamHandler(sys.stdout)
    LOG.addHandler(STDOUT_HANDLER)

    main()
