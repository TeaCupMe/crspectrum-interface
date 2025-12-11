from ISParser import ISParser
from serial import Serial
from utils import YUV2RGB
import struct
import time
from tqdm import tqdm
import numpy

CHUNK_SIZE = 240

class Frame:
    yPixels:list[int]
    uvPixels:list[int]
    def __init__(self):
        self.yPixels = [0] * 90000
        self.uvPixels = [0] * 90000

class CrSpectrum:
    ser:Serial
    imageProperties = dict()
    imageBytes:bytes= bytes()
    currentFilter:int = 0
    
    frame1:Frame = Frame()
    frame2:Frame = Frame()
    
    def __init__(self, selectedCom, baudrate) -> None:
        self.ser = Serial(selectedCom, baudrate=baudrate)
    
    def openSerial(self):
        if not self.ser.is_open:
            self.ser.open()
    def closeSerial(self):
        self.ser.close()
    def getProperties(self) -> dict:
        self.ser.write(b'p')
        self.ser.read_until(b"\xFF\xFF\x00")
        st = self.ser.read_until(b"\x00\xFF\x00")
        self.imageProperties = ISParser.parseImageProperties(bytes(st)[:-3])
        return self.imageProperties
    
    def takePicture(self):
        self.ser.write(b"t")
        self.ser.read_until(b"\x46\x72\x61\x6D\x65\x20\x65\x76\x65\x6E\x74\x0A")
        self.ser.write(b'T')
        print(f"Image taken in {struct.unpack('<H', self.ser.read(2))[0]} milliseconds")
    
    def changeFilter(self):
        self.ser.write(b'f')
        print("Filter changed")
        self.currentFilter = 1 if self.currentFilter == 0 else 0
        
    def getFilter(self):
        return self.currentFilter
        
    
    def getImage(self):
        self.imageBytes = bytes()
        self.ser.timeout = 0.05
        readData = b''
        for i in tqdm(range(1500)):
            while len(readData) < 240:
                self.ser.write(b'c')
                self.ser.write(struct.pack('<H', i))
                readData = self.ser.read(242)[2:]
                if (len(readData)) < 240:
                    print(f"Timeout on chunk {i}, retrying...")
            self.imageBytes += readData
            readData = b''
        self.ser.timeout = None
        numbers = list(map(int, self.imageBytes))
        pixels = [numbers[i*2+1]*256 + numbers[i*2] for i in range(len(numbers)//2)]
        uvPixels = pixels[1::2]
        # yPixels = pixels[::2]
        # b = numpy.array(yPixels).reshape((300, 300))/1024
        image = [(pixels[i*2], pixels[i*2 + (3 if i%2==0 else 1)], pixels[i*2 + (1 if i%2==0 else -1)]) for i in range(len(pixels)//2)]
        yuvFrame = YUV2RGB(numpy.array(image).reshape((300, 300, 3))/4)
        with open("image_"+time.strftime("%H_%M_%S")+"_2.txt", "w+") as f:
            f.write(" ".join(list(map(hex, numbers))))
        return yuvFrame
    
    def getImageChunk(self, chunk:int):
        self.ser.timeout = 0.05
        readData = b''
        while len(readData) < 240:
            self.ser.write(b'c')
            self.ser.write(struct.pack('<H', chunk))
            readData = self.ser.read(242)[2:]
        numbers = list(map(int, readData))
        pixels = [numbers[i*2+1]*256 + numbers[i*2] for i in range(len(numbers)//2)]
        # uvPixels = pixels[1::2]
        # yPixels = pixels[::2]
        # b = numpy.array(yPixels).reshape((300, 300))/1024
        image = [(pixels[i*2], pixels[i*2 + (3 if i%2==0 else 1)], pixels[i*2 + (1 if i%2==0 else -1)]) for i in range(len(pixels)//2)]
        yuvFrame = YUV2RGB(numpy.array(image).reshape((60,1, 3))/4)
        if self.currentFilter == 0:
            self.frame1.uvPixels[chunk*60:(chunk+1)*60] = pixels[1::2]
            self.frame1.yPixels[chunk*60:(chunk+1)*60] = pixels[::2]
        else:
            self.frame2.uvPixels[chunk*60:(chunk+1)*60] = pixels[1::2]
            self.frame2.yPixels[chunk*60:(chunk+1)*60] = pixels[::2]
        if chunk == 1499:
            print(f"sum of pixels with filter 1 is {sum(self.frame1.yPixels)}")
            print(f"sum of pixels with filter 2 is {sum(self.frame2.yPixels)}")
        return yuvFrame.reshape((60, 3)).astype(int)
        
    def getNextChunk(self, ser: Serial) -> dict:
        ser.write(b'n')
        ser.flush()
        # print("next chunk request sent")
        ser.read_until(b"\xFF\xFF\x00")
        chunk = ISParser.parseImageChunk(ser.read(CHUNK_SIZE+6))
        return chunk

        
    def setExposure(self, value: int, ser: Serial):
        ser.write(b'e')
        ser.write(value.to_bytes(2, 'little'))
        
    def setSize(self, width:int, height:int, ser: Serial):
        ser.write(b's')
        ser.write(width.to_bytes(2, 'little'))
        ser.write(height.to_bytes(2, 'little'))