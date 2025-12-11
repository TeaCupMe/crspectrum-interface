import sys
from qtdesigner.CM_Interface_UI import Ui_MainWindow
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTime
# from ISSerial import getPorts
from CrSpectrum import CrSpectrum
from serial import Serial
import serial.tools.list_ports
from time import time, sleep
import numpy as np
from PIL import Image, ImageQt
import os 

from utils import *

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.widgets import Button
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar

class MplCanvas(FigureCanvas):
    fig:Figure
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
    def addSubplot(self, position) -> Axes:
        return self.fig.add_subplot(position)
    
    def axes(self) -> list[Axes]:
        return self.fig.axes

class CameraInterfaceApp(QtWidgets.QMainWindow, Ui_MainWindow):
    debugUI = False
    debugInterface = False
    portOpen:bool = False
    camera:CrSpectrum
    frame1Scene:QtWidgets.QGraphicsScene
    frame1Pixmap:QtWidgets.QGraphicsPixmapItem
    
    frame2Scene:QtWidgets.QGraphicsScene
    frame2Pixmap:QtWidgets.QGraphicsPixmapItem
    
    frameNdviScene:QtWidgets.QGraphicsScene
    frameNdviPixmap:QtWidgets.QGraphicsPixmapItem
    
    frameExtra1Scene:QtWidgets.QGraphicsScene
    frameExtra1Pixmap:QtWidgets.QGraphicsPixmapItem
    
    frameExtra2Scene:QtWidgets.QGraphicsScene
    frameExtra2Pixmap:QtWidgets.QGraphicsPixmapItem
    
    currentPixmap:QtWidgets.QGraphicsPixmapItem
    
    ndviCanvas:MplCanvas
    ndviAx1:Axes
    ndviAx2:Axes
    
    ndviAx1Cb:Colorbar
    ndviAx2Cb:Colorbar

    
    def __init__(self, debugInterface = False, debugUI = False):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.py
        self.debugUI = debugUI
        self.debugInterface = debugInterface
        
        
        super().__init__()
        
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.setWindowIcon(QtGui.QIcon(scriptDir + os.path.sep + 'icon.png'))
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.getImageBar.setValue(0)
        self.clearLabels()
        self.updateComPortsList()
        self.updateSpeedsList()
        
        self.frame1Scene = QtWidgets.QGraphicsScene(self)
        self.frame1View.setScene(self.frame1Scene)
        self.frame1Pixmap = self.frame1Scene.addPixmap(QtGui.QPixmap())

        self.frame2Scene = QtWidgets.QGraphicsScene(self)
        self.frame2View.setScene(self.frame2Scene)
        self.frame2Pixmap = self.frame2Scene.addPixmap(QtGui.QPixmap())
        
        self.frameNdviScene = QtWidgets.QGraphicsScene(self)
        self.frameNdviView.setScene(self.frameNdviScene)
        self.frameNdviPixmap = self.frameNdviScene.addPixmap(QtGui.QPixmap())
        
        self.frameExtra1Scene = QtWidgets.QGraphicsScene(self)
        self.frameExtra1View.setScene(self.frameExtra1Scene)
        self.frameExtra1Pixmap = self.frameExtra1Scene.addPixmap(QtGui.QPixmap())
        
        self.frameExtra2Scene = QtWidgets.QGraphicsScene(self)
        self.frameExtra2View.setScene(self.frameExtra2Scene)
        self.frameExtra2Pixmap = self.frameExtra2Scene.addPixmap(QtGui.QPixmap())
        
        self.ndviCanvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.ndviAx1 = self.ndviCanvas.addSubplot(121)
        self.ndviAx2 = self.ndviCanvas.addSubplot(122)
        self.frameSelector.addTab(self.ndviCanvas, "NDVI MPL")
        
    def clearLabels(self):
        self.exposureLabel.setText("")
        self.widthLabel.setText("")
        self.heightLabel.setText("")
        self.chunksLabel.setText("")
        
    def takePictureButtonPressed(self):
        self.displayDebugTextInTerminal("'Take Picture' pressed")
        self.camera.takePicture()
        self.status.showMessage(f"Image taken with filter {self.camera.currentFilter}")

    def getImageButtonPressed(self):
        self.displayDebugTextInTerminal("'Get Image' pressed")
        self.getImage()
        
    def getImagePropertiesButtonPressed(self):
        self.displayDebugTextInTerminal("'Get Image Properties' pressed")  
        self.getImageProperties()
        
    def setSizeButtonPressed(self):
        self.displayDebugTextInTerminal("'Set Size' pressed")
        self.setSize()

    def setExposureButtonPressed(self):
        value = self.exposureInput.text()
        self.displayDebugTextInTerminal(f"'Set Exposure' pressed with value {value}")
        self.setExposure()
        
    def refreshComPorts(self):
        self.updateComPortsList()
    
    def openClosePort(self):
        if self.portOpen:
            self.camera.closeSerial()
            self.status.showMessage(f"Closed port {self.portSelectorComboBox.currentText()}")
        else:
            self.camera = CrSpectrum(self.portSelectorComboBox.currentText(), int(self.speedSelectorComboBox.currentText()))
            self.camera.openSerial()
            self.status.showMessage(f"Opened port {self.portSelectorComboBox.currentText()} @ {int(self.speedSelectorComboBox.currentText())} baud")
            
        self.portOpen = not self.portOpen
        
        self.OpenComButton.setText("Close" if self.portOpen else "Open")
        
    def changeFilter(self):
        self.camera.changeFilter()
        
    def getNdvi(self):
        self.camera.takePicture()
        self.status.showMessage(f"Image taken with filter {self.camera.currentFilter}")
        self.getImage()
        self.changeFilter()
        self.camera.takePicture()
        self.status.showMessage(f"Image taken with filter {self.camera.currentFilter}")
        self.getImage()

    def getCameraFilter(self):
        return self.camera.currentFilter
            
    def displayDebugTextInTerminal(self, content:str, formatting = None):
        if self.debugUI:    
            self.terminalTextBrowser.insertPlainText("[DEBUG] " + content + "\n")
            self.terminalTextBrowser.verticalScrollBar().setValue(self.terminalTextBrowser.verticalScrollBar().maximum())
        
    def displayTextInTerminal(self, content:str):
        self.terminalTextBrowser.insertPlainText(content)
        self.terminalTextBrowser.verticalScrollBar().setValue(self.terminalTextBrowser.verticalScrollBar().maximum())
        
    def updateComPortsList(self):
        ports = [com for com, _, _ in sorted(serial.tools.list_ports.comports())]
        self.portSelectorComboBox.clear()
        self.portSelectorComboBox.addItems(ports)
    
    def updateSpeedsList(self):
        speeds = [
            "2000000",
            "230400",
            "1000000",
        ]
        self.speedSelectorComboBox.clear()
        self.speedSelectorComboBox.addItems(speeds)
    
    def getImageProperties(self):
        with Serial(self.portSelectorComboBox.currentText(), int(self.speedSelectorComboBox.currentText()), timeout = 3) as serial:
            properties = self.camera.getProperties()
            self.displayDebugTextInTerminal("Received image properties: " + str(properties))
            self.exposureLabel.setText(str(properties["exposure"]))
            self.chunksLabel.setText(str(properties["numberOfChunks"]))
            self.widthLabel.setText(str(properties["width"]))
            self.heightLabel.setText(str(properties["height"]))
        
    def getImage(self):
        if self.getCameraFilter() == 1:
            currentPixmap = self.frame2Pixmap
        else:
            currentPixmap = self.frame1Pixmap           
        
        image = Image.new("RGB", (300, 300))
        imageData = [tuple([0, 0, 0])] * (300*300)
            
        for chunkIndex in range(1500):
            chunk = self.camera.getImageChunk(chunkIndex)
            self.displayDebugTextInTerminal(f"Chunk {chunkIndex} received!")
            QtWidgets.QApplication.instance().processEvents() # type: ignore

            for i in range(len(chunk)):
                imageData[60*chunkIndex+i] = tuple(chunk[i])
            image.putdata(imageData)
            currentPixmap.setPixmap(QtGui.QPixmap(ImageQt.toqpixmap(image)))
            self.getImageBar.setValue(int(chunkIndex*100/1500))
        
        self.getImageBar.setValue(100)
        
        if self.frame1View.scene() != None and self.frame2View.scene() != None:
            self.updateNDVI()
            self.updateExtras()
                 
    def updateNDVI(self):
        
        yFrame1 = np.array(self.camera.frame1.yPixels).reshape((300, 300))
        yFrame2 = np.array(self.camera.frame2.yPixels).reshape((300, 300))
        ndvi1 = (yFrame1 - yFrame2)/ (yFrame1 + yFrame2)
        ndvi2 = (yFrame2 - yFrame1)/ (yFrame1 + yFrame2)
        
        self.ndviAx1.cla()
        self.ndviAx2.cla()
        
        while (len(self.ndviCanvas.axes()) > 2):
            self.ndviCanvas.fig.delaxes(self.ndviCanvas.axes()[-1])
        
        im = self.ndviAx1.imshow(ndvi1, cmap="hot", interpolation="nearest")
        self.ndviAx1.set_title("NDVI if filter 1 is NIR")

        self.ndviAx1Cb = self.ndviCanvas.fig.colorbar(im)
        
        im = self.ndviAx2.imshow(ndvi2, cmap="hot", interpolation="nearest")
        self.ndviAx2.set_title("NDVI if filter 2 is NIR")

        self.ndviAx2Cb = self.ndviCanvas.fig.colorbar(im)

        self.ndviCanvas.draw()
        self.displayDebugTextInTerminal("NDVI updated")
        self.status.showMessage("NDVI updated")
    
    def updateExtras(self):
        image = Image.new("L", (300, 300))
        pixels = self.camera.frame1.yPixels + self.camera.frame1.uvPixels
        pixels[::2] = self.camera.frame1.yPixels
        pixels[1::2] = self.camera.frame1.uvPixels
        
        frame = [(pixels[i*2], pixels[i*2 + (3 if i%2==0 else 1)], pixels[i*2 + (1 if i%2==0 else -1)]) for i in range(len(pixels)//2)]
        rgbImage = YUV2RGB(numpy.array(frame).reshape((300, 300, 3))/4)
        image.putdata(rgbImage[:, :, 0].flatten())
        self.frameExtra1Pixmap.setPixmap(QtGui.QPixmap(ImageQt.toqpixmap(image)))
        
        pixels = self.camera.frame2.yPixels + self.camera.frame2.uvPixels
        pixels[::2] = self.camera.frame2.yPixels
        pixels[1::2] = self.camera.frame2.uvPixels
        
        frame = [(pixels[i*2], pixels[i*2 + (3 if i%2==0 else 1)], pixels[i*2 + (1 if i%2==0 else -1)]) for i in range(len(pixels)//2)]
        rgbImage = YUV2RGB(numpy.array(frame).reshape((300, 300, 3))/4)
        image.putdata(rgbImage[:, :, 0].flatten())
        self.frameExtra2Pixmap.setPixmap(QtGui.QPixmap(ImageQt.toqpixmap(image)))
        pass
    
    def takePicture(self):
        with Serial(self.portSelectorComboBox.currentText(), int(self.speedSelectorComboBox.currentText()), timeout = 3) as serial:
            t = time()
            self.camera.takePicture()
            self.displayTextInTerminal(f"Image taken in {(time() - t):.3f} seconds")
    
    def setExposure(self):
        with Serial(self.portSelectorComboBox.currentText(), int(self.speedSelectorComboBox.currentText()), timeout = 3) as serial:
            value:str = self.exposureInput.text()
            if not value.isdigit():
                self.displayTextInTerminal("Введите желаемое значение экспозиции!\n")
                return
            intValue = int(value)
            if intValue>509:
                self.displayTextInTerminal("Значение экспозиции не может быть больше 509!\n")
            self.camera.setExposure(intValue, serial)
    
    def setSize(self):
        with Serial(self.portSelectorComboBox.currentText(), int(self.speedSelectorComboBox.currentText()), timeout = 3) as serial:         
            width:str = self.widthInput.text()
            height:str = self.heightInput.text()
            
            if not (width.isdigit() and height.isdigit()):
                self.displayTextInTerminal("Введите значения ширины и высоты!\n")
                return
            intWidth = int(width)
            intHeight = int(height)
            if intHeight <= 0 or intHeight > 480:
                self.displayTextInTerminal("Высота должна быть в диапазоне 1-480\n")
                return
            if intWidth <= 0 or intWidth > 640:
                self.displayTextInTerminal("Ширина должна быть в диапазоне 1-640\n")
                return
            
            self.camera.setSize(intWidth, intHeight, serial)
        
        
def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = CameraInterfaceApp(False, True)  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec()  # и запускаем приложение
    
    
if __name__ == "__main__":
    main()