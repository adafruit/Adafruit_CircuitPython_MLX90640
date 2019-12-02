import time
import board
import busio
import mlx90640

PRINT_TEMPERATURES = False
PRINT_ASCIIART = True

i2c = busio.I2C(board.SCL, board.SDA,  frequency=800000)
while not i2c.try_lock():
    pass
print("I2C addresses found:", [hex(device_address)
                               for device_address in i2c.scan()])
i2c.unlock()
mlx = mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C")
print([hex(i) for i in mlx.serial_number])

frame = [0] * 768
while True:
    mlx.getFrame(frame)
    for h in range(24):
        for w in range(32):
            t = frame[h*32 + w]
            if PRINT_TEMPERATURES:
                print("%0.1f, " % t, end="")
            if PRINT_ASCIIART:
                c = '&'
                if t < 20: c = ' '
                elif t < 23: c = '.'
                elif t < 25: c = '-'
                elif t < 27: c = '*'
                elif t < 29: c = '+'
                elif t < 31: c = 'x'
                elif t < 33: c = '%'
                elif t < 35: c = '#'
                elif t < 37: c = 'X'
                print(c, end="")
        print()
    print()
        
