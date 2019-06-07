import os
import serial
from time import sleep
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.common import ModbusClientMixin

mySerial = serial.Serial('/dev/ttyACM0', 115200)
#clientTCP = ModbusTcpClient('192.168.0.55')

for i in range(33):
    msg = '01:'+str(i)
    mySerial.write(msg)
    clientTCP = ModbusTcpClient('192.168.0.55')
    sleep(3)
    Request = clientTCP.read_input_registers(0x0003, 0x0001, unit=0x00)
    clientTCP.close()
    try:
        msg = str(i*100) + ';' + str(Request.registers)
        print(msg)
        path = os.getcwd() + '/database/4curve.ods'
        arq = open(path, 'a')
        arq.write(msg + '\n')
        arq.close()
    except:
        print('Error durante leitura do ModBus TCP')