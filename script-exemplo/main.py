#! /usr/bin/python
# -*- coding: utf-8 -*-

import minimalmodbus
import math
import string
import random
import json

import os
from time import sleep
from subprocess import call
from bitarray import bitarray
import time

from binascii import hexlify
from binascii import unhexlify
from threading import Thread
from SlaveRTU import slaveRTU
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.common import ModbusClientMixin

print('                                                    Modbus Script                                                  ')
print('----------------------------------------------------------------------------------------------------------------')
print('')

start_time = time.time()

AddrTCP = '192.168.0.55'
#AddrTCP = '127.0.0.1'
COMserial = slaveRTU('/dev/ttyUSB0', 9600)
#sglobal = ''

print('Endereco IP do servidor: ' + AddrTCP)
print(COMserial) 

contpacketOK = 0
contpacketERRO = 0

def PacketCompare(function_code, packet, resp):  #faz a comparação do pacote do RTU com o pacote do TCP
    global contpacketOK
    global contpacketERRO
    if function_code == 'FC01' or function_code == 'FC02' or function_code == 'FC03' or function_code == 'FC04':
        sizePacket = int(len(packet))
        sizeHeader = int(len(packet[0:6]))
        sizeCRC = int(len(packet[(sizePacket-4):sizePacket]))
        dado = packet[sizeHeader:(sizePacket-4)]
        if dado == resp:
            contpacketOK = contpacketOK + 1
            return ('Pacote OK: ' + dado)
        else:
            contpacketERRO = contpacketERRO + 1
            return ('Erro de pacote: ' + dado)

    elif function_code == 'FC05':
        function = packet[8:12]
        status = ''
        if function == 'ff00' or function == 'FF00':
            status = True
        elif function == '0000':
            status = False
        if status == resp:
            contpacketOK = contpacketOK + 1
            return('Pacote OK: ' + str(status))
        else:
            contpacketERRO = contpacketERRO + 1
            return ('Erro de pacote: ' + str(status))

    elif function_code == 'FC06'or function_code == 'FC16' or function_code == 'FC15':
        function = packet[8:12]
        function = (int(function, 16))
        if function == resp:
            contpacketOK = contpacketOK + 1
            return('Pacote OK: ' + str(function))
        else:
            contpacketERRO = contpacketERRO + 1
            return ('Erro de pacote: ' + str(function))

def _strGenerator(size=9, chars=string.ascii_uppercase + string.digits):      #gera os pacotes aleatórios
    return ''.join(random.choice(chars) for _ in range(size))

def calcPacket(nAllrequested, function_code):   #calcula o numero de bytes solicitados no pacote
	if function_code == '01' or function_code == '02':
		
		nAllrequested = int(nAllrequested)	

		response = nAllrequested/8.0
		response = math.ceil(response)
		response = int(response)
		return response
	else:
		nAllrequested = int(nAllrequested)
		response = nAllrequested*2
		return response

def makePacket(msg, function_code):                     #processa o pacote de acordo com a solicitação
    packet = json.loads('{}')
    sizeMSG = int(len(msg))
    coilrequested = msg[8:12]
    function_code = msg[2:4]
    if function_code == '01' or function_code == '02':
        coilrequested = (int(coilrequested, 16))
        x = calcPacket(coilrequested, function_code)
        packet['bytevetor'] = ''
        for criaVetor in range(sizeMSG):
            packet['bytevetor'] += _strGenerator(size=x, chars='0123456789ABCDEF')
        message = packet['bytevetor']
        y = x*2
        message = message[0:y]
        return message
    else:
        packet['bytevetor'] = ''
        coilrequested = (int(coilrequested, 16))
        x = calcPacket(coilrequested, function_code)
        for criaVetor in range(sizeMSG):
            packet['bytevetor'] += _strGenerator(size=x, chars='0123456789ABCDEF')
        message = packet['bytevetor']
        y = x*2
        message = message[0:y]
        return message

def reversePacket(function_code, Request):
    try:
        if function_code == 'FC01' or function_code == 'FC02':
            vet = Request.bits
            resp = 0
            counter = 0
            for bit in vet:
                resp += bit << counter
                counter += 1
            #print hex(resp)
            vetor = hex(resp)
            vetor = vetor.replace('0x','')
            vetor_ord = ''
            size = int(len(vetor))
            for i in range(size, 0, -1):
                if i % 2 == 0:
                    y = i - 2
                    vetor_ord += chr(int(vetor[y:i], 16))    
            return (hexlify(vetor_ord))
        elif function_code == 'FC03' or function_code == 'FC04':
            vet = Request.registers
            resp = ''
            for register in vet:
                resp += hex(register)
            vetor = resp.replace('0x','')
            return vetor

        elif function_code == 'FC05' or function_code == 'FC06':
            return Request.value
        
        elif function_code == 'FC15' or function_code == 'FC10':
            return Response.count

    except:
        return 'Erro'
        sleep(0.5)

def slave():    #Recebe as MSN do RTU do MSF e depois envia novamente uma nova para o RTU do MSF     
    global sglobal
    sglobal = ''
    while(1):
        bytevetor = ''
        message = hexlify(COMserial.receive_packet())
        #print('[<<] '+message)
        address = str(message[0:2])
        function_code = str(message[2:4])
        if function_code == '01' or function_code == '02' or function_code == '03' or function_code == '04':
            bytevetor = str(makePacket(message, message[2:4]))
            PacketCalc = (int(message[8:12], 16))
            PacketCalc = str(calcPacket(PacketCalc, message[2:4]))
        elif function_code == '05' or function_code == '06' or function_code == '0F' or function_code == '0f' or function_code == '10':
            PacketCalc = str(message[4:6])
            bytevetor = str(message[6:12])
   
        sglobal = COMserial.Send_packet(address, function_code, PacketCalc, bytevetor)
        sglobal = hexlify(sglobal)
        #print('[>>] '+sglobal)

thread1 = Thread(target=slave) 
thread1.start()

def times():
    sleep(0.25)

a = 1
contpacket = 0

while a:
    #function_code = raw_input('>')
    for function_code in ['01','02','03','04','05','06','0f','10']:
    #for function_code in ['0f']:
        #------------------------------------------------------------------------
        if function_code == '01':
            clientTCP = ModbusTcpClient(AddrTCP)
            connection = clientTCP.connect()
            #print(clientTCP.timeout)
            if connection == True:
                times()
                print('--------------------------------------------------FC01---------------------------------------------------------- ') 
                Request = clientTCP.read_coils(0x0013, 0x0025, unit=0x11)
                resp = reversePacket('FC01', Request)
                print('')
                print('*********************************************************')
                print('Resultado comparado com Modbus RTU:')
                print(PacketCompare('FC01', sglobal, resp))
                print('')
                print('Resposta do Modbus TCP:')
                print(Request)
                print('')
                print('Valor do Modbus TCP: ' + resp)
                print('*********************************************************')
                contpacket = contpacket + 1
                clientTCP.close()
                times()
            else:
                a = 0

        elif function_code == '02':
            clientTCP = ModbusTcpClient(AddrTCP)
            connection = clientTCP.connect()
            #print(clientTCP.timeout)
            if connection == True:
                times()
                print('--------------------------------------------------FC02----------------------------------------------------------')
                Request = clientTCP.read_discrete_inputs(0x00C4, 0x0016, unit=0x11)
                resp = reversePacket('FC02', Request)
                print('')
                print('*********************************************************')
                print('Resultado comparado com Modbus RTU:')
                print(PacketCompare('FC02', sglobal, resp))
                print('')
                print('Resposta do Modbus TCP:')
                print(Request)
                print('')
                print('Valor do Modbus TCP: ' + resp)
                print('*********************************************************')
                contpacket = contpacket + 1
                clientTCP.close()
                times()
            else:
                a = 0

        elif function_code == '03':
            clientTCP = ModbusTcpClient(AddrTCP)
            connection = clientTCP.connect()
            #print(clientTCP.timeout)
            if connection == True:
                times()
                print('--------------------------------------------------FC03----------------------------------------------------------')
                Request = clientTCP.read_holding_registers(0x006B, 0x0003, unit=0x11)
                resp = reversePacket('FC03', Request)
                print('')
                print('*********************************************************')
                print('Resultado comparado com Modbus RTU:')
                print(PacketCompare('FC03', sglobal, resp))
                print('')
                print('Resposta do Modbus TCP:')
                print(Request)
                print('')
                print('Valor do Modbus TCP: ' + resp)
                print('*********************************************************')
                contpacket = contpacket + 1
                clientTCP.close()
                times()
            else:
                a = 0

        elif function_code == '04':
            clientTCP = ModbusTcpClient(AddrTCP)
            connection = clientTCP.connect()
            #print(clientTCP.timeout)
            if connection == True:
                times()
                print('--------------------------------------------------FC04----------------------------------------------------------')
                Request = clientTCP.read_input_registers(0x0008, 0x0001, unit=0x11)
                resp = reversePacket('FC04', Request)
                print('')
                print('*********************************************************')
                print('Resultado comparado com Modbus RTU:')
                print(PacketCompare('FC04', sglobal, resp))
                print('')
                print('Resposta do Modbus TCP:')
                print(Request)
                print('')
                print('Valor do Modbus TCP: ' + resp)
                print('*********************************************************')
                contpacket = contpacket + 1
                clientTCP.close()
                times()
            else:
                a = 0

        elif function_code == '05':
            clientTCP = ModbusTcpClient(AddrTCP)
            connection = clientTCP.connect()
            #print(clientTCP.timeout)
            if connection == True:
                times()
                print('--------------------------------------------------FC05----------------------------------------------------------')
                Response = clientTCP.write_coil(0x00AC, 0xFF00, unit=0x11)
                resp = reversePacket('FC05', Response)
                print('')
                print('*********************************************************')
                print('Resultado comparado com Modbus RTU:')
                print(PacketCompare('FC05', sglobal, resp))
                print('')
                print('Resposta do Modbus TCP:')
                print(Response)
                print('')
                print('Valor do Modbus TCP: ' + str(resp))
                print('*********************************************************')
                contpacket = contpacket + 1
                clientTCP.close()
                times()
            else:
                a = 0

        elif function_code == '06':
            clientTCP = ModbusTcpClient(AddrTCP)
            connection = clientTCP.connect()
            #print(clientTCP.timeout)
            if connection == True:
                times()
                print('--------------------------------------------------FC06----------------------------------------------------------')
                Response = clientTCP.write_register(0x0001, 0x0003, unit=0x11)
                resp = reversePacket('FC06', Response)
                print('')
                print('*********************************************************')
                print('Resultado comparado com Modbus RTU:')
                print(PacketCompare('FC06', sglobal, resp))
                print('')
                print('Resposta do Modbus TCP:')
                print(Response)
                print('')
                print('Valor do Modbus TCP: ' + str(resp))
                print('*********************************************************')
                contpacket = contpacket + 1
                clientTCP.close()
                times()
            else:
                a = 0

        elif function_code == '0f':
            clientTCP = ModbusTcpClient(AddrTCP)
            connection = clientTCP.connect()
            #print(clientTCP.timeout)
            if connection == True:
                times()
                print('--------------------------------------------------FC15----------------------------------------------------------')
                vetor = [0x000A, 0x0102]
                Response = clientTCP.write_coils(0x0013, vetor, unit=0x11)
                resp = reversePacket('FC15', Response)
                print('')
                print('*********************************************************')
                print('Resultado comparado com Modbus RTU:')
                print(PacketCompare('FC15', sglobal, resp))
                print('')
                print('Resposta do Modbus TCP:')
                print(Response)
                print('')
                print('Valor do Modbus TCP: ' + str(resp))
                print('*********************************************************')
                contpacket = contpacket + 1
                clientTCP.close()
                times()
            else:
                a = 0

        elif function_code == '10':
            clientTCP = ModbusTcpClient(AddrTCP)
            connection = clientTCP.connect()
            #print(clientTCP.timeout)
            if connection == True:
                times()
                print('--------------------------------------------------FC16----------------------------------------------------------')
                vetor = [0x000A, 0x0102]
                Response = clientTCP.write_registers(0x0001, vetor, unit=0x11)
                resp = reversePacket('FC10', Response)
                print('')
                print('*********************************************************')
                print('Resultado comparado com Modbus RTU:')
                print(PacketCompare('FC16', sglobal, resp))
                print('')
                print('Resposta do Modbus TCP:')
                print(Response)
                print('')
                print('Valor do Modbus TCP: ' + str(resp))
                print('*********************************************************')
                contpacket = contpacket + 1
                clientTCP.close()
            else:
                a = 0
        
        elapsed_time = time.time() - start_time

print('Total de tempo gasto no teste:')
print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
print('')
print('Total de pacotes enviados: ')
print(contpacket)
print('Total de pacotes OK: ')
print(contpacketOK)
print('Total de pacotes ERRO: ')
print(contpacketERRO)
