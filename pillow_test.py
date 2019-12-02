"""This example is for Raspberry Pi (Linux) only!
   It will not work on microcontrollers running CircuitPython!"""


import time
import board
import busio
import os
import math
import numpy as np
import pygame
from colour import Color
from PIL import Image

import mlx90640

INTERPOLATE = 10

# Set i2c freq to 1MHz in /boot/config.txt
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
falsecolors = (Color("black"), Color("indigo"), Color("green"),  Color("yellow"),
               Color("red"), Color("purple"), Color("white"))
#how many color values we can have
COLORDEPTH = (len(falsecolors)-1) * 50
colors = []
for i in range(len(falsecolors)-1):
    colors += list(falsecolors[i].range_to(falsecolors[i+1], 50))
print(COLORDEPTH, len(colors))
#create the array of colors
colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

pygame.mouse.set_visible(False)
screen.fill((255, 0, 0))
pygame.display.update()
screen.fill((0, 0, 0))
pygame.display.update()
sensorout = pygame.Surface((32, 24))

#some utility functions
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


#initialize the sensor
mlx = mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C, Serial #", [hex(i) for i in mlx.serial_number])
mlx.refresh_rate = mlx90640.RefreshRate.REFRESH_32_HZ
print(mlx.refresh_rate)
print("refresh rate: ", pow(2, (mlx.refresh_rate-1)), "Hz")

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
        pixels[i] = colors[coloridx]

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


