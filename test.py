import time
import board
import busio
import mlx90640

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
    try:
        mlx.getFrame(frame)
    except RuntimeError as e:
        print(e)
        print("#" * 40)
        print("retrying...")
