import serial
import serial.tools
import serial.tools.list_ports

def getPorts():
    return [com for com, _, _ in sorted(serial.tools.list_ports.comports())]

class ISSerial:
    ser:serial.Serial
    
    # def __init__(self, ser:serial.Serial) -> None:
    #     self.ser = ser
        
    def __init__(self, port:str, speed:int = 230400) -> None:
        self.ser = serial.Serial(port, speed, timeout=10)
        
        
    
    