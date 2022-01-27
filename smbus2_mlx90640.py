from adafruit_mlx90640 import RefreshRate
import adafruit_mlx90640
import struct

def splitlen_array(data, length):
    """
    Breaks `data` into chunks of size `length`.

    splitlen_array(['a', 'b', 'c', 'd'], 2) == [('a', 'b'), ('c', 'd')]
    
    Note: this function will drop any remainder data:

    splitlen_array(['a', 'b', 'c'], 2) == [('a', 'b')]
    """
    return list(zip(*[ data[z::length] for z in range(length) ]))

class MLX90640(adafruit_mlx90640.MLX90640):
    def __init__(self, smbus2_bus, address=0x33):
        self.bus = smbus2_bus
        self.address = address
        self.eeData = [0] * 832
        self._I2CReadWords(0x2400, self.eeData)
        # print(self.eeData)
        self._ExtractParameters()

    def _I2CWriteWord(self, writeAddress, data):
        import smbus2
        cmd = [0] * 4
        cmd[0] = writeAddress >> 8
        cmd[1] = writeAddress & 0xff
        cmd[2] = data >> 8
        cmd[3] = data & 0xff
        write_packet = smbus2.i2c_msg.write(self.address, cmd)
        self.bus.i2c_rdwr(write_packet)

    def _I2CReadWords(self, addr, buf, *, end=None):
        import smbus2
        if end is None:
            readlen = len(buf)
        else:
            readlen = end
        write_packet = smbus2.i2c_msg.write(self.address, list(struct.pack(">H", addr)))
        read_packet = smbus2.i2c_msg.read(self.address, readlen * 2)
        self.bus.i2c_rdwr(write_packet, read_packet)
        ret_data = [ struct.unpack(">H", bytes(x))[0] for x in splitlen_array(bytes(read_packet), 2) ]
        for i, val in enumerate(ret_data):
            buf[i] = val
