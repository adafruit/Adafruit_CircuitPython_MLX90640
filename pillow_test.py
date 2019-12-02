"""This example is for Raspberry Pi (Linux) only!
   It will not work on microcontrollers running CircuitPython!"""


import time
import board
import busio
import os
import math
import numpy as np
import pygame
from scipy.interpolate import griddata
from colour import Color

import mlx90640

PRINT_TEMPERATURES = False
PRINT_ASCIIART = True

# Set i2c freq to 1MHz in /boot/config.txt
i2c = busio.I2C(board.SCL, board.SDA)

#low range of the sensor (this will be blue on the screen)
MINTEMP = 22.
#high range of the sensor (this will be red on the screen)
MAXTEMP = 35.
#how many color values we can have
COLORDEPTH = 1024
INTERPOLATION = 3

# set up display
os.environ['SDL_FBDEV'] = "/dev/fb0"
os.environ['SDL_VIDEODRIVER'] = "fbcon"
pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
print(pygame.display.Info())

#sensor is an 32x24 grid, multiply by desired interpolation
width = INTERPOLATION * 32
height = INTERPOLATION * 24
displayPixelWidth = pygame.display.Info().current_w//width
displayPixelHeight = pygame.display.Info().current_h//height


# pylint: disable=invalid-slice-index
points = [(math.floor(ix % 32), math.floor(ix / 32)) for ix in range(0, 24*32)]
grid_x, grid_y = np.mgrid[0:31:width*1j, 0:24:height*1j]
# pylint: enable=invalid-slice-index

#the list of colors we can choose from
blue = Color("indigo")
colors = list(blue.range_to(Color("red"), COLORDEPTH))

#create the array of colors
colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

pygame.mouse.set_visible(False)
screen.fill((255, 0, 0))
pygame.display.update()
screen.fill((0, 0, 0))
pygame.display.update()
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

    pixels = [map_value(p, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1) for p in frame]
    #perform interpolation
    bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')
    #draw everything
    for jy, col in enumerate(bicubic):
        for ix, pixel in enumerate(col):
            if np.isnan(pixel):
                continue
            pygame.draw.rect(screen,
                             colors[constrain(int(pixel), 0, COLORDEPTH-1)],
                             (displayPixelWidth * jy, displayPixelHeight * ix,
                              displayPixelWidth, displayPixelHeight))
    pygame.display.update()
    print("Processed 2 frames in %0.2f s" % (time.monotonic()-stamp))

