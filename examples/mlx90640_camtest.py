"""This example is for Raspberry Pi (Linux) only!
   It will not work on microcontrollers running CircuitPython!"""


import time
import board
import busio
import os
import math
import numpy as np
import pygame
from PIL import Image

import adafruit_mlx90640

INTERPOLATE = 10

# MUST et I2C freq to 1MHz in /boot/config.txt
i2c = busio.I2C(board.SCL, board.SDA)

#low range of the sensor (this will be black on the screen)
MINTEMP = 20.
#high range of the sensor (this will be white on the screen)
MAXTEMP = 50.

# set up display
os.environ['SDL_FBDEV'] = "/dev/fb0"
os.environ['SDL_VIDEODRIVER'] = "fbcon"
pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
print(pygame.display.Info())

#the list of colors we can choose from
heatmap = (
    (0.0, (0, 0, 0)),
    (0.20, (0, 0, .5)),
    (0.40, (0, .5, 0)),
    (0.60, (.5, 0, 0)),
    (0.80, (.75, .75, 0)),
    (0.90, (1.0, .75, 0)),
    (1.00, (1.0, 1.0, 1.0)),
)

#how many color values we can have
COLORDEPTH = 1000

colormap = [0] * COLORDEPTH

#some utility functions
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def gaussian(x, a, b, c, d=0):
    return a * math.exp(-(x - b)**2 / (2 * c**2)) + d

def gradient(x, width=100, map=[], spread=1):
    width = float(width)
    r = sum([gaussian(x, p[1][0], p[0] * width, width/(spread*len(map))) for p in map])
    g = sum([gaussian(x, p[1][1], p[0] * width, width/(spread*len(map))) for p in map])
    b = sum([gaussian(x, p[1][2], p[0] * width, width/(spread*len(map))) for p in map])
    r = int(constrain(r*255, 0, 255))
    g = int(constrain(g*255, 0, 255))
    b = int(constrain(b*255, 0, 255))
    return r, g, b

for i in range(COLORDEPTH):
    colormap[i] = gradient(i, COLORDEPTH, map=heatmap)

pygame.mouse.set_visible(False)
screen.fill((255, 0, 0))
pygame.display.update()
screen.fill((0, 0, 0))
pygame.display.update()
sensorout = pygame.Surface((32, 24))


#initialize the sensor
mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C, Serial #", [hex(i) for i in mlx.serial_number])
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_32_HZ
print(mlx.refresh_rate)
print("Refresh rate: ", pow(2, (mlx.refresh_rate-1)), "Hz")

frame = [0] * 768
while True:
    stamp = time.monotonic()
    try:
        mlx.getFrame(frame)
    except ValueError:
        continue        # these happen, no biggie - retry
    
    print("Read 2 frames in %0.2f s" % (time.monotonic()-stamp))

    pixels = [0] * 768
    for i, pixel in enumerate(frame):
        coloridx = map_value(pixel, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1)
        coloridx = int(constrain(coloridx, 0, COLORDEPTH-1))
        pixels[i] = colormap[coloridx]

    for h in range(24):
        for w in range(32):
            pixel = pixels[h*32 + w]
            sensorout.set_at((w, h), pixel)

    #pixelrgb = [colors[constrain(int(pixel), 0, COLORDEPTH-1)] for pixel in pixels]
    img = Image.new('RGB', (32, 24))
    img.putdata(pixels)
    img = img.resize((32*INTERPOLATE, 24*INTERPOLATE), Image.BICUBIC) 
    img_surface = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
    pygame.transform.scale(img_surface.convert(), screen.get_size(), screen)
    pygame.display.update()
    print("Completed 2 frames in %0.2f s (%d FPS)" %
          (time.monotonic()-stamp, 1.0 / (time.monotonic()-stamp)))


