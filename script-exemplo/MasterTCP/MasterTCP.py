import pymodbus
import logging

from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusTcpClient

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

client = ModbusTcpClient('127.0.0.1')
client.write_coil(1, True)
result = client.read_coils(1,1)
print(result.bits[0])
