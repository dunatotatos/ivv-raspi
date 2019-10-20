import time
from w1thermsensor import W1ThermSensor
from w1thermsensor.errors import ResetValueError
sensor = W1ThermSensor()

while True:
    try:
        temperature = sensor.get_temperature()
    except ResetValueError:
        print("Temperature sensor sent the reset value.")
    print("The temperature is %s celsius" % temperature)
    time.sleep(1)

#declenchement à 30 c°
