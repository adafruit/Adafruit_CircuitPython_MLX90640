from adafruit_bus_device.i2c_device import I2CDevice
import struct
import math

eeData = [0] * 832
I2C_READ_LEN = 100
SCALEALPHA = 0.000001

class MLX90640:
    """Interface to the MLX90640 temperature sensor."""
    kVdd = 0
    vdd25 = 0
    KvPTAT = 0
    KtPTAT = 0
    vPTAT25 = 0
    alphaPTAT = 0
    gainEE = 0
    tgc = 0
    KsTa = 0
    resolutionEE = 0
    calibrationModeEE = 0
    ksTo = [0] * 5
    ct = [0] * 5
    alpha = [0] * 768
    alphaScale = 0
    offset = [0] * 768
    kta = [0] * 768
    ktaScale = 0
    kv = [0] * 768
    kvScale = 0
    cpAlpha = [0] * 2
    cpOffset = [0] * 2
    ilChessC = [0] * 3
    brokenPixels = [0xFFFF] * 5
    outlierPixels = [0xFFFF] * 5

    def __init__(self, i2c_bus, address=0x33):
        self.i2c_device = I2CDevice(i2c_bus, address)
        self._I2CReadWords(0x2400, eeData)
        #print(eeData)
        self._ExtractParameters()


    def _ExtractParameters(self):
        self._ExtractVDDParameters()
        self._ExtractPTATParameters()
        self._ExtractGainParameters()
        self._ExtractTgcParameters()
        self._ExtractResolutionParameters()
        self._ExtractKsTaParameters()
        self._ExtractKsToParameters()
        self._ExtractCPParameters()
        self._ExtractAlphaParameters()
        self._ExtractOffsetParameters()
        self._ExtractKtaPixelParameters()
        self._ExtractKvPixelParameters()
        self._ExtractCILCParameters()
        self._ExtractDeviatingPixels()

        # debug output
        """
        print('-'*40)
        print("kVdd = %d, vdd25 = %d" % (self.kVdd, self.vdd25))
        print("KvPTAT = %f, KtPTAT = %f, vPTAT25 = %d, alphaPTAT = %f" %
              (self.KvPTAT, self.KtPTAT, self.vPTAT25, self.alphaPTAT))
        print("Gain = %d, Tgc = %f, Resolution = %d" % (self.gainEE, self.tgc, self.resolutionEE))
        print("KsTa = %f, ksTo = %s, ct = %s" % (self.KsTa, self.ksTo, self.ct))
        print("cpAlpha:", self.cpAlpha, "cpOffset:", self.cpOffset)
        print("alpha: ", self.alpha)
        print("alphascale: ", self.alphaScale)
        print("offset: ", self.offset)\
        print("kta:", self.kta)
        print("ktaScale:", self.ktaScale)
        print("kv:", self.kv)
        print("kvScale:", self.kvScale)
        print("calibrationModeEE:", self.calibrationModeEE)
        print("ilChessC:", self.ilChessC)
        print('-'*40)
        """

        
    def _ExtractVDDParameters(self):
        # extract VDD
        self.kVdd = (eeData[51] & 0xFF00) >> 8
        if self.kVdd > 127:
            self.kVdd -= 256   # convert to signed
        self.kVdd *= 32
        self.vdd25 = eeData[51] & 0x00FF;
        self.vdd25 = ((self.vdd25 - 256) << 5) - 8192

    def _ExtractPTATParameters(self):
        # extract PTAT
        self.KvPTAT = (eeData[50] & 0xFC00) >> 10
        if self.KvPTAT > 31:
            self.KvPTAT -= 64
        self.KvPTAT /= 4096
        self.KtPTAT = eeData[50] & 0x03FF
        if self.KtPTAT > 511:
            self.KtPTAT -= 1024
        self.KtPTAT /= 8
        self.vPTAT25 = eeData[49]
        self.alphaPTAT = (eeData[16] & 0xF000) / math.pow(2, 14) + 8

    def _ExtractGainParameters(self):
        # extract Gain
        self.gainEE = eeData[48]
        if self.gainEE > 32767:
            self.gainEE -= 65536

    def _ExtractTgcParameters(self):
        # extract Tgc
        self.tgc = eeData[60] & 0x00FF
        if self.tgc > 127:
            self.tgc -= 256
        self.tgc /= 32

    def _ExtractResolutionParameters(self):
        # extract resolution
        self.resolutionEE = (eeData[56] & 0x3000) >> 12

    def _ExtractKsTaParameters(self):
        # extract KsTa
        self.KsTa = (eeData[60] & 0xFF00) >> 8
        if self.KsTa > 127:
            self.KsTa -= 256
        self.KsTa /= 8192

    def _ExtractKsToParameters(self):
        # extract ksTo
        step = ((eeData[63] & 0x3000) >> 12) * 10
        self.ct[0] = -40
        self.ct[1] = 0
        self.ct[2] = (eeData[63] & 0x00F0) >> 4
        self.ct[3] = (eeData[63] & 0x0F00) >> 8
        self.ct[2] *= step
        self.ct[3] = self.ct[2] + self.ct[3]*step
    
        KsToScale = (eeData[63] & 0x000F) + 8
        KsToScale = 1 << KsToScale

        self.ksTo[0] = eeData[61] & 0x00FF
        self.ksTo[1] = (eeData[61] & 0xFF00) >> 8
        self.ksTo[2] = eeData[62] & 0x00FF
        self.ksTo[3] = (eeData[62] & 0xFF00) >> 8
    
        for i in range(4):
            if self.ksTo[i] > 127:
                self.ksTo[i] -= 256
            self.ksTo[i] /= KsToScale
        self.ksTo[4] = -0.0002

    def _ExtractCPParameters(self):
        # extract CP
        offsetSP = [0] * 2
        alphaSP = [0] * 2
        
        alphaScale = ((eeData[32] & 0xF000) >> 12) + 27
    
        offsetSP[0] = eeData[58] & 0x03FF
        if offsetSP[0] > 511:
            offsetSP[0] -= 1024    

        offsetSP[1] = (eeData[58] & 0xFC00) >> 10
        if offsetSP[1] > 31:
            offsetSP[1] -= 64
        offsetSP[1] += offsetSP[0]
    
        alphaSP[0] = eeData[57] & 0x03FF
        if alphaSP[0] > 511:
            alphaSP[0] -= 1024
        alphaSP[0] /= math.pow(2, alphaScale)
    
        alphaSP[1] = (eeData[57] & 0xFC00) >> 10
        if alphaSP[1] > 31:
            alphaSP[1] -= 64
        alphaSP[1] = (1 + alphaSP[1]/128) * alphaSP[0]
    
        cpKta = eeData[59] & 0x00FF
        if cpKta > 127:
            cpKta -= 256
        ktaScale1 = ((eeData[56] & 0x00F0) >> 4) + 8
        self.cpKta = cpKta / math.pow(2, ktaScale1)
    
        cpKv = (eeData[59] & 0xFF00) >> 8
        if cpKv > 127:
            cpKv -= 256
        kvScale = (eeData[56] & 0x0F00) >> 8
        self.cpKv = cpKv / math.pow(2, kvScale)
       
        self.cpAlpha[0] = alphaSP[0]
        self.cpAlpha[1] = alphaSP[1]
        self.cpOffset[0] = offsetSP[0]
        self.cpOffset[1] = offsetSP[1]

    def _ExtractAlphaParameters(self):
        # extract alpha
        accRemScale = eeData[32] & 0x000F
        accColumnScale = (eeData[32] & 0x00F0) >> 4
        accRowScale = (eeData[32] & 0x0F00) >> 8
        alphaScale = ((eeData[32] & 0xF000) >> 12) + 30
        alphaRef = eeData[33]
        accRow = [0]*24
        accColumn = [0]*32
        alphaTemp = [0] * 768

        for i in range(6):
            p = i * 4
            accRow[p + 0] = (eeData[34 + i] & 0x000F)
            accRow[p + 1] = (eeData[34 + i] & 0x00F0) >> 4
            accRow[p + 2] = (eeData[34 + i] & 0x0F00) >> 8
            accRow[p + 3] = (eeData[34 + i] & 0xF000) >> 12

        for i in range(24):
            if accRow[i] > 7:
                accRow[i] -= 16

        for i in range(8):
            p = i * 4;
            accColumn[p + 0] = (eeData[40 + i] & 0x000F)
            accColumn[p + 1] = (eeData[40 + i] & 0x00F0) >> 4
            accColumn[p + 2] = (eeData[40 + i] & 0x0F00) >> 8
            accColumn[p + 3] = (eeData[40 + i] & 0xF000) >> 12

        for i in range(32):
            if accColumn[i] > 7:
                accColumn[i] -= 16

        for i in range(24):
            for j in range(32):
                p = 32 * i + j
                alphaTemp[p] = (eeData[64 + p] & 0x03F0) >> 4
                if alphaTemp[p] > 31:
                    alphaTemp[p] -= 64
                alphaTemp[p] *= 1 << accRemScale
                alphaTemp[p] += alphaRef + (accRow[i] << accRowScale) + (accColumn[j] << accColumnScale)
                alphaTemp[p] /= math.pow(2, alphaScale)
                alphaTemp[p] -= self.tgc * (self.cpAlpha[0] + self.cpAlpha[1])/2
                alphaTemp[p] = SCALEALPHA / alphaTemp[p]
        #print("alphaTemp: ", alphaTemp)

        temp = max(alphaTemp)
        #print("temp", temp)
        
        alphaScale = 0
        while temp < 32768:
            temp *= 2
            alphaScale += 1

        for i in range(768):
            temp = alphaTemp[i] * math.pow(2, alphaScale)
            self.alpha[i] = int(temp + 0.5)

        self.alphaScale = alphaScale

    def _ExtractOffsetParameters(self):
        # extract offset
        occRow = [0] * 24
        occColumn = [0] * 32

        occRemScale = (eeData[16] & 0x000F)
        occColumnScale = (eeData[16] & 0x00F0) >> 4
        occRowScale = (eeData[16] & 0x0F00) >> 8
        offsetRef = eeData[17]
        if offsetRef > 32767:
            offsetRef -= 65536

        for i in range(6):
            p = i * 4
            occRow[p + 0] = (eeData[18 + i] & 0x000F)
            occRow[p + 1] = (eeData[18 + i] & 0x00F0) >> 4
            occRow[p + 2] = (eeData[18 + i] & 0x0F00) >> 8
            occRow[p + 3] = (eeData[18 + i] & 0xF000) >> 12

        for i in range(24):
            if occRow[i] > 7:
                occRow[i] -= 16

        for i in range(8):
            p = i * 4
            occColumn[p + 0] = (eeData[24 + i] & 0x000F)
            occColumn[p + 1] = (eeData[24 + i] & 0x00F0) >> 4
            occColumn[p + 2] = (eeData[24 + i] & 0x0F00) >> 8
            occColumn[p + 3] = (eeData[24 + i] & 0xF000) >> 12

        for i in range(32):
            if occColumn[i] > 7:
                occColumn[i] -= 16

        for i in range(24):
            for j in range(32):
                p = 32 * i + j
                self.offset[p] = (eeData[64 + p] & 0xFC00) >> 10
                if self.offset[p] > 31:
                    self.offset[p] -= 64
                self.offset[p] *= 1 << occRemScale
                self.offset[p] += offsetRef + (occRow[i] << occRowScale) + (occColumn[j] << occColumnScale)

    def _ExtractKtaPixelParameters(self):
        # extract KtaPixel
        KtaRC = [0] * 4
        ktaTemp = [0] * 768
    
        KtaRoCo = (eeData[54] & 0xFF00) >> 8
        if KtaRoCo > 127:
            KtaRoCo -= 256
        KtaRC[0] = KtaRoCo
    
        KtaReCo = eeData[54] & 0x00FF
        if KtaReCo > 127:
            KtaReCo -= 256
        KtaRC[2] = KtaReCo
      
        KtaRoCe = (eeData[55] & 0xFF00) >> 8
        if KtaRoCe > 127:
            KtaRoCe -= 256
        KtaRC[1] = KtaRoCe
      
        KtaReCe = eeData[55] & 0x00FF
        if KtaReCe > 127:
            KtaReCe -= 256
        KtaRC[3] = KtaReCe
  
        ktaScale1 = ((eeData[56] & 0x00F0) >> 4) + 8
        ktaScale2 = (eeData[56] & 0x000F)

        for i in range(24):
            for j in range(32):
                p = 32 * i + j
                split = 2*(p//32 - (p//64)*2) + p%2
                ktaTemp[p] = (eeData[64 + p] & 0x000E) >> 1
                if ktaTemp[p] > 3:
                    ktaTemp[p] -= 8
                ktaTemp[p] *= 1 << ktaScale2
                ktaTemp[p] += KtaRC[split]
                ktaTemp[p] /= math.pow(2, ktaScale1)
                # ktaTemp[p] = ktaTemp[p] * mlx90640->offset[p];

        temp = abs(ktaTemp[0])
        for kta in ktaTemp:
            temp = max(temp, abs(kta))
                
        ktaScale1 = 0
        while temp < 64:
            temp *= 2
            ktaScale1 += 1
     
        for i in range(768):
            temp = ktaTemp[i] * math.pow(2, ktaScale1)
            if temp < 0:
                self.kta[i] = int(temp - 0.5)
            else:
                self.kta[i] = int(temp + 0.5);
        self.ktaScale = ktaScale1


    def _ExtractKvPixelParameters(self):
        KvT = [0] * 4
        kvTemp = [0] * 768

        KvRoCo = (eeData[52] & 0xF000) >> 12
        if KvRoCo > 7:
            KvRoCo -= 16
        KvT[0] = KvRoCo

        KvReCo = (eeData[52] & 0x0F00) >> 8
        if KvReCo > 7:
            KvReCo -= 16
        KvT[2] = KvReCo
      
        KvRoCe = (eeData[52] & 0x00F0) >> 4
        if KvRoCe > 7:
            KvRoCe -= 16
        KvT[1] = KvRoCe
      
        KvReCe = eeData[52] & 0x000F
        if KvReCe > 7:
            KvReCe -= 16
        KvT[3] = KvReCe
  
        kvScale = (eeData[56] & 0x0F00) >> 8
        
        for i in range(24):
            for j in range(32):
                p = 32 * i + j
                split = 2*(p//32 - (p//64)*2) + p%2
                kvTemp[p] = KvT[split]
                kvTemp[p] /= math.pow(2, kvScale)
                #kvTemp[p] = kvTemp[p] * mlx90640->offset[p];

        temp = abs(kvTemp[0])
        for kv in kvTemp:
            temp = max(temp, abs(kv))

        kvScale = 0
        while temp < 64:
            temp *= 2
            kvScale += 1

        for i in range(768):
            temp = kvTemp[i] * math.pow(2, kvScale)
            if temp < 0:
                self.kv[i] = int(temp - 0.5)
            else:
                self.kv[i] = int(temp + 0.5)
        self.kvScale = kvScale

    def _ExtractCILCParameters(self):
        ilChessC = [0] * 3
    
        self.calibrationModeEE = (eeData[10] & 0x0800) >> 4
        self.calibrationModeEE = self.calibrationModeEE ^ 0x80

        ilChessC[0] = eeData[53] & 0x003F
        if ilChessC[0] > 31:
            ilChessC[0] -= 64
        ilChessC[0] /= 16.0
    
        ilChessC[1] = (eeData[53] & 0x07C0) >> 6
        if ilChessC[1] > 15:
            ilChessC[1] -= 32
        ilChessC[1] /= 2.0
    
        ilChessC[2] = (eeData[53] & 0xF800) >> 11
        if ilChessC[2] > 15:
            ilChessC[2] -= 32
        ilChessC[2] /= 8.0
    
        self.ilChessC = ilChessC

    def _ExtractDeviatingPixels(self):
        self.brokenPixels = [0xFFFF] * 5
        self.outlierPixels = [0xFFFF] * 5

        pixCnt = 0
        brokenPixCnt = 0
        outlierPixCnt = 0
         
        while (pixCnt < 768) and (brokenPixCnt < 5) and (outlierPixCnt < 5):
            if eeData[pixCnt+64] == 0:
                self.brokenPixels[brokenPixCnt] = pixCnt
                brokenPixCnt += 1
            elif (eeData[pixCnt+64] & 0x0001) != 0:
                self.outlierPixels[outlierPixCnt] = pixCnt
                outlierPixCnt += 1
            pixCnt += 1
    
        if brokenPixCnt > 4:
            raise RuntimeError("More than 4 broken pixels")
        if outlierPixCnt > 4:
            raise RuntimeError("More than 4 outlier pixels")
        if (brokenPixCnt + outlierPixCnt) > 4:
            raise RuntimeError("More than 4 faulty pixels")
        print("Found %d broken pixels, %d outliers" % (brokenPixCnt, outlierPixCnt))
        # TODO INCOMPLETE

    def _I2CReadWords(self, addr, buffer):
        remainingWords = len(buffer)
        offset = 0
        addrbuf = bytearray(2)
        inbuf = bytearray(2 * I2C_READ_LEN)
        with self.i2c_device as i2c:
            while remainingWords:
                addrbuf[0] = addr >> 8    # MSB
                addrbuf[1] = addr & 0xFF  # LSB
                read_words = min(remainingWords, I2C_READ_LEN)
                i2c.write(addrbuf, stop=False)
                i2c.readinto(inbuf, end=read_words*2) # in bytes
                outwords = struct.unpack('>' + 'H' * read_words, inbuf[0:read_words*2])
                for i, w in enumerate(outwords):
                    buffer[offset+i] = w
                offset += read_words
                remainingWords -= read_words
                addr += read_words
        #print([hex(i) for i in buffer])
