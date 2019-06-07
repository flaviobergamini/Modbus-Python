import os
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.common import ModbusClientMixin
from time import sleep

while 1:
    clientTCP = ModbusTcpClient('192.168.0.55')
    sleep(0.2)
    connection = clientTCP.connect()
    if connection == True:
        Request = clientTCP.read_discrete_inputs(0x0000, 0x0004, unit=0x00)
        resp = Request.bits
        print(resp)
        clientTCP.close()
    else:
        print('Conexao com o dispositivo nao estabelecida')
