#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import dbus
import dbus.service
import inspect
import pprint
import os
import sys
import time

from threading import Thread
import can
import struct

# our own packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '../'))
from vedbus import VeDbusService

softwareVersion = '1.0'

def createDBusEntriesForDCShunt(deviceinstance):
    dcshunt_dbusservice = VeDbusService('com.victronenergy.battery.masterbus_shunt0', dbus.SystemBus(private=True))
    dcshunt_dbusservice.add_path('/Mgmt/ProcessName', __file__)
    dcshunt_dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ')
    dcshunt_dbusservice.add_path('/Mgmt/Connection', __file__ + ' connection')

    # Create the mandatory objects
    dcshunt_dbusservice.add_path('/DeviceInstance', deviceinstance)
    dcshunt_dbusservice.add_path('/ProductId', 0)
    dcshunt_dbusservice.add_path('/ProductName', 'Mastervolt DC Shunt')
    dcshunt_dbusservice.add_path('/CustomName', 'DCShunt')
    dcshunt_dbusservice.add_path('/FirmwareVersion', 0)
    dcshunt_dbusservice.add_path('/HardwareVersion', 0)
    dcshunt_dbusservice.add_path('/Connected', 1)

    # As defined in https://github.com/victronenergy/venus/wiki/dbus#battery
    dcshunt_dbusservice.add_path('/Dc/0/Voltage', value=None)
    dcshunt_dbusservice.add_path('/Dc/0/Current', value=None)
    dcshunt_dbusservice.add_path('/Dc/0/Power', value=None)
    dcshunt_dbusservice.add_path('/Dc/0/Temperature', value=None)
    dcshunt_dbusservice.add_path('/ConsumedAmphours', value=None)
    dcshunt_dbusservice.add_path('/Soc', value=None)

    dcshunt_dbusservice.add_path('/History/MinimumVoltage', value=None)
    dcshunt_dbusservice.add_path('/History/MaximumVoltage', value=None)
    dcshunt_dbusservice.add_path('/History/LastDischarge', value=None)
    dcshunt_dbusservice.add_path('/History/DeepestDischarge', value=None)

    return dcshunt_dbusservice

DEVICE_ID_MASK=0x0003FFFF
DEVICE_ID_DC_SHUNT=0x31297
DEVICE_ID_MASSCOMBI=0x2f412
DEVICE_ID_MASTERVIEW=0x0840a

MESSAGE_KIND_MASK=0x1FFC0000

ATTR_DCSHUNT_SOC=0x00
ATTR_DCSHUNT_VOLTS=0x01
ATTR_DCSHUNT_AMPS=0x02
ATTR_DCSHUNT_AMPS_CONSUMED=0x03
ATTR_DCSHUNT_TEMPERATURE=0x05


ATTR_INVERTER_STATE=0x020e
ATTR_INVERTER_ON_OR_OFF=0x0014

ATTR_INVERTER_DC_VOLTAGE_IN=0x06
ATTR_INVERTER_DC_AMPS_IN=0x07
ATTR_CHARGER_AC_VOLTAGE_IN=0x08
ATTR_CHARGER_AC_AMPS_IN=0x09
ATTR_INVERTER_AC_VOLTS_OUT=0x0A
ATTR_INVERTER_AC_AMPS_OUT=0x0B
ATTR_INVERTER_INPUT_GENSET=0x0E
XXX_ATTR_INVERTER_STATE=0x10
ATTR_INVERTER_LOAD_PERCENT=0x11
ATTR_CHARGER_STATE=0x12
ATTR_INVERTER_SHORE_FUSE=0x13
ATTR_INVERTER_ON_OFF=0x14
ATTR_INVERTER_ENTER_OFF=0x15
ATTR_MASSCOMBI_POWER_STATE=0x38
ATTR_CHARGER_SWITCH_STATE=0x3A
ATTR_CHARGER_MODE=0x3C

def handleDCShuntMessage(message, messageKind):
    if(message.dlc == 2): return
    if 'dcshunt_dbusservice' not in globals() : return
    
#    print('\tmessageKind=%X' % (messageKind))
    if(0x21b==messageKind):
        global dcshunt_dbusservice
        (attributeId, floatValue)=struct.unpack('<Hf', message.data)
        print('\tdcshunt (attributeId=0x%X, floatValue=%f)' % (attributeId, floatValue))
        if(ATTR_DCSHUNT_SOC==attributeId):
            dcshunt_dbusservice['/Soc']=round(floatValue, 0)
        elif(ATTR_DCSHUNT_VOLTS==attributeId):
            dcshunt_dbusservice['/Dc/0/Voltage']=round(floatValue, 2)
            if dcshunt_dbusservice['/Dc/0/Current'] is not None : dcshunt_dbusservice['/Dc/0/Power']=round(floatValue*dcshunt_dbusservice['/Dc/0/Current'])
            if dcshunt_dbusservice['/History/MinimumVoltage'] is None or dcshunt_dbusservice['/History/MinimumVoltage'] > floatValue:
                dcshunt_dbusservice['/History/MinimumVoltage']=round(floatValue, 2)
            if dcshunt_dbusservice['/History/MaximumVoltage'] is None or dcshunt_dbusservice['/History/MaximumVoltage'] < floatValue:
                dcshunt_dbusservice['/History/MaximumVoltage']=round(floatValue, 2)
        elif(ATTR_DCSHUNT_AMPS==attributeId):
            dcshunt_dbusservice['/Dc/0/Current']=round(floatValue, 2)
            if dcshunt_dbusservice['/Dc/0/Voltage'] is not None : dcshunt_dbusservice['/Dc/0/Power']=round(floatValue*dcshunt_dbusservice['/Dc/0/Voltage'])
        elif(ATTR_DCSHUNT_AMPS_CONSUMED==attributeId):
            dcshunt_dbusservice['/ConsumedAmphours']=round(floatValue, 2)
            if dcshunt_dbusservice['/History/LastDischarge'] is None or dcshunt_dbusservice['/History/LastDischarge'] < floatValue:
                dcshunt_dbusservice['/History/LastDischarge']=round(floatValue, 2)
            
        elif(ATTR_DCSHUNT_TEMPERATURE==attributeId):
            dcshunt_dbusservice['/Dc/0/Temperature']=round(floatValue, 1)
    elif(0x19b==messageKind): #String label messages
        None
    else:
        if(message.dlc>4):
            print('No dcshunt handling for message kind 0x%X' % (messageKind))
            print(message)

def createDBusEntriesForMassCombi(deviceinstance):
    masscombi_dbusservice = VeDbusService('com.victronenergy.inverter.masterbus_masscombi1', dbus.SystemBus(private=True))
    masscombi_dbusservice.add_path('/Mgmt/ProcessName', __file__)
    masscombi_dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ')
    masscombi_dbusservice.add_path('/Mgmt/Connection', __file__ + ' connection')

    # Create the mandatory objects
    masscombi_dbusservice.add_path('/DeviceInstance', deviceinstance)
    masscombi_dbusservice.add_path('/ProductId', 0)
    masscombi_dbusservice.add_path('/ProductName', 'Mastervolt masscombi 4000W')
    masscombi_dbusservice.add_path('/CustomName', 'Masscombi')
    masscombi_dbusservice.add_path('/FirmwareVersion', 0)
    masscombi_dbusservice.add_path('/HardwareVersion', 0)
    masscombi_dbusservice.add_path('/Connected', 1)

    # As defined in https://github.com/victronenergy/venus/wiki/dbus#inverter
    masscombi_dbusservice.add_path('/Dc/0/Voltage', value=None)
    #masscombi_dbusservice.add_path('/Dc/0/Current', value=None)
    masscombi_dbusservice.add_path('/Ac/Out/L1/V', value=120)
    masscombi_dbusservice.add_path('/Ac/Out/L1/I', value=None)
    masscombi_dbusservice.add_path('/Mode', value=2)
    masscombi_dbusservice.add_path('/State', value=9)

    return masscombi_dbusservice

def handleMasscombiMessage(message, messageKind):
    global masscombi_dbusservice
    if(0x020e==messageKind):
        (attributeId, floatValue)=struct.unpack('<Hf', message.data)
        print('\tmasscombi (attributeId=0x%X, floatValue=%f)' % (attributeId, floatValue))
        if(ATTR_INVERTER_STATE==attributeId):
            masscombi_dbusservice['/Mode']=2 #TODO Switch position: 2=Inverter on; 4=Off; 5=Low Power/ECO
            masscombi_dbusservice['/State']=9 #TODO 0=Off; 1=Low Power; 2=Fault; 9=Inverting
        elif(ATTR_INVERTER_AC_AMPS_OUT==attributeId):
            masscombi_dbusservice['/Ac/Out/L1/I']=round(floatValue, 2)
        elif(ATTR_INVERTER_DC_VOLTAGE_IN==attributeId):
            masscombi_dbusservice['/Dc/0/Voltage']=round(floatValue, 2)
        #elif(ATTR_INVERTER_DC_AMPS_IN==attributeId):
            #masscombi_dbusservice['/Dc/0/Current']=round(floatValue, 2)

def parseMasterbusMessage(message):
    #if(message.is_rx==False):
        #return
    deviceId=message.arbitration_id&DEVICE_ID_MASK
    messageKind=(message.arbitration_id&MESSAGE_KIND_MASK)>>18;

    if(deviceId==DEVICE_ID_DC_SHUNT):
        handleDCShuntMessage(message, messageKind);
    elif(deviceId==DEVICE_ID_MASSCOMBI):
        handleMasscombiMessage(message, messageKind);

def handleDBusEvents(mainloop):
    try:
        global bus
        for message in bus:
            parseMasterbusMessage(message)
    except:
        traceback.print_exc()
        mainloop.quit()

def makeMastervoltRequestMessage(deviceId,itemId):
    return can.Message(arbitration_id=deviceId, data=itemId.to_bytes(2,'little'), is_extended_id=True)

def mainForwardMasterbusToDbus():
    global dbusObjects
    print(__file__ + " starting up")

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    global dcshunt_dbusservice
    dcshunt_dbusservice=createDBusEntriesForDCShunt(deviceinstance=0)
    global masscombi_dbusservice
    masscombi_dbusservice=createDBusEntriesForMassCombi(deviceinstance=1)

    global bus
    bus = can.Bus(channel='can1', interface='socketcan')
    periodicMessages=[
        makeMastervoltRequestMessage(0x186F1297, ATTR_DCSHUNT_SOC),
        makeMastervoltRequestMessage(0x186F1297, ATTR_DCSHUNT_VOLTS),
        makeMastervoltRequestMessage(0x186F1297, ATTR_DCSHUNT_AMPS),
        makeMastervoltRequestMessage(0x186F1297, ATTR_DCSHUNT_AMPS_CONSUMED),
    ]
    bus.send_periodic(periodicMessages, 1.0)

    periodicMessages=[
        makeMastervoltRequestMessage(0x183AF412, ATTR_INVERTER_DC_VOLTAGE_IN),
        makeMastervoltRequestMessage(0x183AF412, ATTR_INVERTER_AC_AMPS_OUT),
    ]
    bus.send_periodic(periodicMessages, 1.0)
    
    mainloop = GLib.MainLoop()
    poller = Thread(target=lambda: handleDBusEvents(mainloop))
    poller.daemon = True
    poller.start()
    mainloop.run()

mainForwardMasterbusToDbus()

#Without a terminator, I get 2000 canbus messages in 81 seconds. --->  time candump -n 2000 can1
#If I add a 120 Ohm terminator between Can H and CAN L.
