#!/usr/bin/python
# -*- coding: utf-8 -*-
#

## @file ketCube_LoRaUplink.py
#
# @author Jan Belohoubek
# @version 0.1
# @date    2018-08-12
# @brief   The KETCube uplink test script
#
# @note This script works with loraserver.io network server
# @note Requirements:
#    Standard Python2 installation (Tested in Debian and Fedora with Mosquitto MQTT server...)
#    paho-client: pip install paho-mqtt
#
# @attention
# 
#  <h2><center>&copy; Copyright (c) 2018 University of West Bohemia in Pilsen
#  All rights reserved.</center></h2>
# 
#  Developed by:
#  The SmartCampus Team
#  Department of Technologies and Measurement
#  www.smartcampus.cz | www.zcu.cz
# 
#  Permission is hereby granted, free of charge, to any person obtaining a copy 
#  of this software and associated documentation files (the “Software”), 
#  to deal with the Software without restriction, including without limitation 
#  the rights to use, copy, modify, merge, publish, distribute, sublicense, 
#  and/or sell copies of the Software, and to permit persons to whom the Software 
#  is furnished to do so, subject to the following conditions:
# 
#     - Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimers.
#     
#     - Redistributions in binary form must reproduce the above copyright notice, 
#       this list of conditions and the following disclaimers in the documentation 
#       and/or other materials provided with the distribution.
#     
#     - Neither the names of The SmartCampus Team, Department of Technologies and Measurement
#       and Faculty of Electrical Engineering University of West Bohemia in Pilsen, 
#       nor the names of its contributors may be used to endorse or promote products 
#       derived from this Software without specific prior written permission. 
# 
#  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
#  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
#  PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE CONTRIBUTORS OR COPYRIGHT HOLDERS 
#  BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
#  OR THE USE OR OTHER DEALINGS WITH THE SOFTWARE.

### Imports
import os, urlparse, json, base64
import paho.mqtt.client as paho
import time
import binascii
import getpass

### Settings
DEBUG = True # Debug True/False

MQTT_SERVER="app.loratech.cz"
MQTT_USER="belohoubketzcucz"
MQTT_PASSWD="***"
MQTT_PORT="1883"
MQTT_TIMEOUT=30.0
MQTT_RX_TOPIC="application/1/node/1122334455667788/rx" # CHANGE NODE ID!

MQTT_CONNECTED = False

# Seect QoS level
MQTT_QOS=0 # At most once
#MQTT_QOS=1 # At least once
#MQTT_QOS=2 # Exactly once

### Client
mqttc = paho.Client()

### Event callbacks
def on_connect(mosq, obj, flags, rc):
    global DEBUG, MQTT_RX_TOPIC, MQTT_QOS

    print("MQTT OnConnect :: rc: " + str(rc))
     
    if rc == 0:
        MQTT_CONNECTED = True
    
    # Start subscribe, with QoS level 0
    mqttc.subscribe(MQTT_RX_TOPIC, MQTT_QOS)

def on_disconnect(mosq, obj, rc):
    global mqttc

    if rc != 0:
        print ("MQTT OnDisconnect :: MQTT disconnected unexpectedly. Auto-reconnect ...")
        try:
            mqttc.reconnect()
        except:
            print("FATAL :: Connection with MQTT server lost! ")
            exit(1)
    else:
        print ("MQTT OnDisconnect :: MQTT Disconnect() call.")

def on_message(mosq, obj, msg):
    global DEBUG

    try:
        data = json.loads(msg.payload)
    except:
        print("ERROR :: MQTT Message: not a JSON object; parameter \"" + str(msg.payload) + "\" is of type: " + str(type(msg.payload)))
        return()

    if type(data) is not dict:
        print("ERROR :: MQTT Message: not a JSON object (conversion to dict failed); parameter \"" + str(data) + "\" is of type: " + str(type(data)))
        return()

    try:
        dataASCII = base64.b64decode(data[u'data'])
    except:
        print("WARNING :: Malformed data!")
        dataASCII = "MALFORMED DATA RECEIVED!"

    if DEBUG == True:
        print("MQTT Message :: data type: " + str(type(data)))
        print("MQTT Message :: RAW msg: " + str(data))
        print("MQTT Message :: RAW data: " + str(data[u'data']))
        print("MQTT Message :: dataASCII: " + dataASCII)

    
    devEUI = (data[u'devEUI'])
    fPort = str((data[u'fPort']))
    rxInfo = (data[u'rxInfo'])
    data = (data[u'data'])
    
    # Receive parameters:
    bestRssi=-1000
    bestSNR=0
    GWMac=""
    GWName=""
    for i in range(0, (len(rxInfo))):
        if int((rxInfo[i])[u'rssi']) > bestRssi:
            bestRssi = int((rxInfo[i])[u'rssi'])
            bestSNR = int((rxInfo[i])[u'loRaSNR'])
            GWMac = str((rxInfo[i])[u'mac'])
            GWName = str((rxInfo[i])[u'name'])

    GWCount = len(rxInfo)

    rxBytes = bytearray()
    rxBytes.extend(dataASCII)

    # Print decode and print data
    # Use the following variables: devEUI, fPort, rxInfo, bestRssi, bestSNR, GWMac, GWName, GWCount, data, dataASCII, rxBytes
    print("Msg from " + str(devEUI) + ": " + str(data))
    print "Uint16_t: " + str((rxBytes[1] * 256 + rxBytes[2])/10.0)
    

def on_publish(mosq, obj, mid):
    print("MQTT Publish :: mid: " + str(mid))

def on_subscribe(mosq, obj, mid, granted_qos):
    print("MQTT Subscribe :: mid" + str(mid) + "; qos: " + str(granted_qos))

def on_log(mosq, obj, level, string):
    print("MQTT Log: " + string)


### Main
print("")
print("KETCube uplink test&demo script")
print("-------------------------------")
print("")

print("Here you can replace parameters defined in the script header (dafault values are enclosed in \"[]\"):")
# Get user input

MQTT_SERVER=raw_input("Set MQTT server address or IP [" + MQTT_SERVER + "]:") or str(MQTT_SERVER)
MQTT_PORT=raw_input("Set MQTT server port [" + MQTT_PORT + "]:") or str(MQTT_PORT)
MQTT_USER=raw_input("Set MQTT user name [" + MQTT_USER + "]:") or str(MQTT_USER)
TMP_MQTT_PASSWD = getpass.getpass("Set MQTT password [" + MQTT_PASSWD + "]:")
if TMP_MQTT_PASSWD != "":
    MQTT_PASSWD = TMP_MQTT_PASSWD
MQTT_RX_TOPIC=raw_input("Set MQTT RX topic [" + MQTT_RX_TOPIC + "]:") or str(MQTT_RX_TOPIC)

# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

if DEBUG == True: 
    mqttc.on_log = on_log

# Pripojeni k MQTT serveru
try:
  mqttc.username_pw_set(MQTT_USER, MQTT_PASSWD)
  mqttc.connect(MQTT_SERVER, port=MQTT_PORT, keepalive=30.0)


except:
  print("FATAL :: Connect to MQTT failed!")
  exit(1)

# Continue the network loop, exit when an error occurs
print("Press CTRL+C to terminate!")
print("--------------------------")
print("")

while True:
    retval = mqttc.loop(timeout=10.0)
    if retval != 0:
        try:
            print("MQTT Reconnect (Error : " + str(retval) + ")")
            mqttc.reconnect()
        except:
            print("FATAL :: Connection with MQTT server lost! ")
            break
