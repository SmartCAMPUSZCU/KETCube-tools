#!/usr/bin/python
# -*- coding: utf-8 -*-
#

## @file ketCube_LoRaDownlink.py
#
# @author Jan Belohoubek
# @version 0.1
# @date    2018-05-07
# @brief   The KETCube downlink test script
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
import binascii
import errno
import time
import json
import base64
import getpass

### Settings
DEBUG = True # Debug True/False

MQTT_SERVER="app.loratech.cz"
MQTT_USER="belohoubketzcucz"
MQTT_PASSWD="***"
MQTT_PORT="1883"
MQTT_TIMEOUT=30.0
MQTT_TX_TOPIC="application/1/node/1122334455667788/tx" # CHANGE NODE ID!
TX_PORT=11 # KETCube LoRa port for strings
TX_DATA="HELLO WORLD!"
TX_PERIOD=10 # period in seconds
TX_ITER=1    # number of iterations

MQTT_CONNECTED = False

# Seect QoS level
MQTT_QOS=0 # At most once
#MQTT_QOS=1 # At least once
#MQTT_QOS=2 # Exactly once

### Client
mqttc = paho.Client()

### Event callbacks
def on_connect(mosq, obj, flags, rc):
    global MQTT_TOPIC
    global MQTT_QOS
    global MQTT_CONNECTED

    print("MQTT OnConnect :: rc: " + str(rc))
    
    if rc == 0:
        MQTT_CONNECTED = True

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
    print("MQTT Message :: msg: " + str(msg))

def on_publish(mosq, obj, mid):
    print("MQTT Publish :: mid: " + str(mid))

def on_subscribe(mosq, obj, mid, granted_qos):
    print("MQTT Subscribe :: mid" + str(mid) + "; qos: " + str(granted_qos))

def on_log(mosq, obj, level, string):
    print("MQTT Log: " + string)


### Main
print("")
print("KETCube downlink test&demo script")
print("---------------------------------")
print("")

print("Here you can replace parameters defined in the script header (dafault values are enclosed in \"[]\"):")
# Get user input

MQTT_SERVER=raw_input("Set MQTT server address or IP [" + MQTT_SERVER + "]:") or str(MQTT_SERVER)
MQTT_PORT=raw_input("Set MQTT server port [" + MQTT_PORT + "]:") or str(MQTT_PORT)
MQTT_USER=raw_input("Set MQTT user name [" + MQTT_USER + "]:") or str(MQTT_USER)
TMP_MQTT_PASSWD = getpass.getpass("Set MQTT password [" + MQTT_PASSWD + "]:")
if TMP_MQTT_PASSWD != "":
    MQTT_PASSWD = TMP_MQTT_PASSWD
MQTT_TX_TOPIC=raw_input("Set MQTT TX topic [" + MQTT_TX_TOPIC + "]:") or str(MQTT_TX_TOPIC)

TX_DATA = raw_input("Set TX data [" + TX_DATA + "]:") or str(TX_DATA)
tmp_ITER = raw_input("Set number of identical messages you would like to send (0 == inf) [" + str(TX_ITER) + "]:")
try:
    TX_ITER = int(tmp_ITER)
except:
    pass
    
if TX_ITER != 1:
    tmp_PERIOD = raw_input("Set period of sending (send TX data every [" + str(TX_PERIOD) + "] seconds):")
    try:
        TX_PERIOD = int(tmp_PERIOD)
    except:
        pass

# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

if DEBUG == True: 
    mqttc.on_log = on_log

# Connect to MQTT server
try:
  mqttc.username_pw_set(MQTT_USER, MQTT_PASSWD)
  mqttc.connect(MQTT_SERVER, port=MQTT_PORT, keepalive=MQTT_TIMEOUT)
  retval = mqttc.loop(timeout=TX_PERIOD)

except:
  print("FATAL :: Connect to MQTT failed!")
  exit(1)

# Continue the network loop, exit when an error occurs
print("Press CTRL+C to terminate!")
print("--------------------------")
print("")

while True:
    print("Runnig iterration #" + str(TX_ITER) + " ... ")
    retval = mqttc.loop(timeout=TX_PERIOD)
    time.sleep(TX_PERIOD)
    if (MQTT_CONNECTED == False):
        try:
            print("MQTT Reconnect (Not conected!)")
            mqttc.reconnect()
            continue
        except:
            print("FATAL :: Connection to MQTT server lost! ")
            break

    data = base64.b64encode(TX_DATA)
    dataJson = '{"reference": "abcd1234", "confirmed": false, "fPort": ' + str(TX_PORT) + ', "data": "' + str(data) + '"}'
    mqttc.publish(MQTT_TX_TOPIC, payload=dataJson, qos=MQTT_QOS, retain=False)

    if (TX_ITER == 0):
        continue
    elif (TX_ITER == 1):
        print("")
        print("Bye!")
        break
    else:
        TX_ITER = TX_ITER - 1

    time.sleep(TX_PERIOD)

print("")
exit(0)
