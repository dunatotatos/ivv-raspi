import RPi.GPIO as RPI
bird = 21
RPI.setmode(RPI.BCM)
RPI.setup(bird, RPI.OUT)
RPI.output(bird, True)
