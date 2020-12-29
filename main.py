import RPi.GPIO as GPIO
import subprocess
import time
import logging
import sys
from w1thermsensor import W1ThermSensor
from w1thermsensor.errors import ResetValueError

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
        self.activated = False
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
        Check if the sensor is active, and send a request to Houdini.

        This method combines self.read and self.get_request in a simple
        one-shot method.

        """
        if self.read() and not self.activated:
            LOG.debug("Activate %s sensor.\n", self.name_get)
            self.activated = True
            self.get_request()
            return True
        return False


class Thermometer(Sensor):
    """
    A sensor which reads a difference of temperature since its creation.

    Due to the very specific usage in this room, this class includes the
    activation of a relay.

    int difference: minimum temperature difference needed to activate.

    """

    def __init__(self, *args, **kwargs):
        self.difference = kwargs.pop('difference')
        super(Thermometer, self).__init__(pin=0, *args, **kwargs)

        # Automatically find where the thermometer is connected.
        self.sensor = W1ThermSensor()
        self.start_temperature = 0  # To set with self.start

    def start(self):
        """Set starting temperature."""
        self.start_temperature = self.safe_get_temperature()

    def safe_get_temperature(self):
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
                current_temperature = self.sensor.get_temperature()
            except ResetValueError:
                nb_exceptions += 1
                LOG.warning(
                    "Temperature sensor sent reset value %s times. Ignoring.",
                    nb_exceptions)
                if nb_exceptions >= 10:
                    LOG.error("%s %s",
                              "Maximum number of hardware failures reached. ",
                              "Stopping...")
                    raise
            else:
                LOG.debug("Current temperature: %s.\n",
                          str(current_temperature))
                return current_temperature
            time.sleep(0.01)

    def read(self):
        """
        Check if the temperature raised wince starting of the game.

        Return the result as boolean

        """
        floor_temperature = self.start_temperature + self.difference
        return self.safe_get_temperature() > floor_temperature


def tonneau_callback():
    """
    Scenario to trigger when temperature is raised.

    Turns on the moine, wait for the end of the soundtrack,
    then trigger the bird flight.

    """
    GPIO.output(constant.MOINE_GPIO, True)
    time.sleep(61)
    GPIO.output(constant.BIRD_GPIO, True)
    time.sleep(50)
    GPIO.output(constant.BIRD_GPIO, False)


class Game:
    """
    One game instance.

    This class provides an interface to manage the logic of a game.
    Instanciate this class to create a new game instance, and run game.start
    to wait for the start button signal.

    """

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(constant.BIRD_GPIO, GPIO.OUT)
        GPIO.setup(constant.MOINE_GPIO, GPIO.OUT)

        self.sensors = {
            'start': Sensor(constant.START_GPIO, "start"),
            'atelier': Sensor(constant.ATELIER_GPIO, "atelier"),
            'caveau': Sensor(constant.CAVEAU_GPIO, "caveau"),
            'serre': Sensor(constant.SERRE_GPIO, "serre"),
            'tonneau': Thermometer(name_get="temperature", difference=2),
        }
        self.sensors['tonneau'].start()

    def wait_start(self):
        """Do nothing until the start button is pressed, then exit."""
        while not self.sensors['start'].read():
            time.sleep(0.1)
        self.sensors['start'].activated = True
        LOG.info("Start button pressed.\n")
        subprocess.call(
            ["curl", "-X", "GET", "{}start".format(constant.URL_DST)])
        time.sleep(5)
        subprocess.call(
            ["curl", "-X", "GET", "{}machine".format(constant.URL_DST)])

    def run(self):
        """Wait for events to send triggers."""
        while not self.is_complete():
            LOG.debug("Check atelier.\n")
            self.sensors['atelier'].check_run()
            LOG.debug("Check caveau.\n")
            self.sensors['caveau'].check_run()
            LOG.debug("Check serre.\n")
            self.sensors['serre'].check_run()
            LOG.debug("Check temperature.")
            if self.sensors['tonneau'].check_run():
                tonneau_callback()
            time.sleep(0.1)

    def start(self):
        """
        Start a new game.

        Wait for the start signal, then listen for sensor update to trigger
        the associated action.

        """
        LOG.info("Start service.\n")

        try:
            LOG.debug("Wait for game start.\n")
            self.wait_start()
            LOG.debug("Game started.\n")
            self.run()
        finally:
            GPIO.cleanup()
            LOG.info("Stop service.")

    def is_complete(self):
        """
        Check if the Game instance still has something to do before next game.

        Return True if Game is complete. False otherwise.

        """
        return self.sensors['tonneau'].activated


if __name__ == "__main__":
    LOG.setLevel(logging.INFO)
    STDOUT_HANDLER = logging.StreamHandler(sys.stdout)
    LOG.addHandler(STDOUT_HANDLER)

    while True:
        Game().start()
