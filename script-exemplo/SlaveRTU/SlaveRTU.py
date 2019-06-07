#! /usr/bin/python
# -*- coding: utf-8 -*-

from binascii import hexlify
from binascii import unhexlify

import serial
import json
import minimalmodbus

class slaveRTU(object): 
    def __init__(self, port, baudrate):                                   #Recebe os dados para realizar um conexão serial
        self.COMserial = serial.Serial(port, baudrate=baudrate)
    
    def receive_packet(self):                                             #Recebe um pacote da serial
        message = self.COMserial.read(2)                                  #unhexlify(str("1103006B00037687"))
        test = hexlify(message)[2:4]
        if test == '01' or test == '02' or test == '03'or test == '04'or test == '05' or test == '06':
            message += self.COMserial.read(6)
        elif test == '0f':
            message += self.COMserial.read(8)
        elif test == '10':
            message += self.COMserial.read(11)
        else:
            raise Exception
        #print(message)
        return message
      
    def Send_packet(self, slaveaddr, registerfunc, nsizebyte, bytevetor):  #Envia um pacote para a serial
        message = self.buildPacket(slaveaddr, registerfunc, nsizebyte, bytevetor)
        #print(message)
        self.COMserial.write(message)
        return message 

    def buildPacket(self, slaveaddr, registerfunc, nsizebyte, bytevetor):
        address = chr(int(slaveaddr, 16))
        function_code = chr(int(registerfunc, 16))
        sizepacket = chr(int(nsizebyte, 16))
        sizebvetor = int(len(bytevetor))

        bytevetorFinal = ''
        for x in range(sizebvetor):  #Monta um vetor para os dados recebidos das funções modbus
            if x % 2 == 0:
                y = x + 2
                bytevetorFinal += chr(int(bytevetor[x:y], 16))
    
        read_device = address + function_code + sizepacket + bytevetorFinal 

        crc = minimalmodbus._calculateCrcString(read_device)
        crc = crc[0]+crc[1]
        
        message = ''
        message += address + function_code + sizepacket + bytevetorFinal + crc
        return message

        