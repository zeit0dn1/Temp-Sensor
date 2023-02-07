#created by Keith Gill 2023
#uses RPI Pico W, ds1820 temp sensors with a small OLED to display and publish temp sensor data to HomeAssistant using MQTT autodiscovery
#developed using 4 sensors

#todo:
# improve docs on github
# make it temp scale agnostic.  F or C

#NB: config secrets.py and mysensors.py

import machine, network, secrets
import onewire
import ds18x20
import utime,time,math
import binascii
import ntptime
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from umqtt.simple import MQTTClient
from machine import WDT
import mysensors

#set up our watchdog timer to 8.3 sec
wdt = WDT(timeout=8300)

#set up wlan and mqtt
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
                                                                                                                                
#to list all SSID's seen
#print (wlan.scan())                                     
wlan.connect(secrets.SSID, secrets.PASSWORD)

#to test if we are connected
#print(wlan.isconnected())

#pet the dog
wdt.feed()

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
  if wlan.status() < 0 or wlan.status() >= 3:
    break
  max_wait -= 1
  print('waiting for connection...')
  time.sleep(1)
  #pet the dog
  wdt.feed()
# Handle connection error
if wlan.status() != 3:
    #let the watchdog timer reset the system
    time.sleep(10)
    raise RuntimeError('network connection failed')
else:
  print('connected')
  status = wlan.ifconfig()
  print( 'ip = ' + status[0] )
  
def sub_cb(topic, msg):
    print(msg)

def connect_and_subscribe():
  #global client_id, mqtt_server, topic_sub
  client = MQTTClient(secrets.CLIENT,secrets.MQTTHOST,user=secrets.MQTTUSER, password=secrets.MQTTPASS, keepalive=300, ssl=False, ssl_params={})
  client.set_callback(sub_cb)
  client.connect()
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

try:
  client = connect_and_subscribe()
except OSError as e:                                                                    
  restart_and_reconnect()

#pet the dog
wdt.feed()

#let's set up the pico to use -6 UTC offset and set the clock properly
ntptime.settime()
rtc = machine.RTC()
#utc_shift = -6
utc_shift = int(secrets.UTCOFFSET)
tm = utime.localtime(utime.mktime(utime.localtime()) + utc_shift*3600)
tm = tm[0:3] + (0,) + tm[3:6] + (0,)
rtc.datetime(tm)

#let's set up the OLED
# Create I2C object
sda = Pin(26)
scl = Pin(27)
i2c = I2C(1, scl=scl, sda=sda, freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

#let's set up the temperature sensors
gp_pin = machine.Pin(20)  #used GP20

ds18b20_sensor = ds18x20.DS18X20(onewire.OneWire(gp_pin))

sensors = ds18b20_sensor.scan()

print('Found devices: ', sensors)

#loop through sensors and publish config to HA for each probe
counter = 1
for device in sensors:
    #we need to make the device id's human readable (stored in binary)
    s = binascii.hexlify(device)
    readable_string = s.decode('ascii')
    
    #print(readable_string)
    
    
    
    #print(secrets.PROBENAME)
    
    #let's publish our HA autodiscovery stuff
    #first the Config topic
    config = b'homeassistant/sensor/' + secrets.PROBENAME + readable_string + b'/config'
    data = b'{"uniq_id":"' + readable_string + b'","name":"Probe ' + readable_string[-4:] + b'", "dev_cla":"temperature", "state_class":"measurement","unit_of_measurement":"' + secrets.SCALE +'", "state_topic":"homeassistant/sensor/' + readable_string + b'/state", "value_template":"{{ value_json.temperature}}" }'
    client.publish(config,data,1) #publish and set it to retain
    counter += 1
    time.sleep_ms(250)
    wdt.feed()
    
#loop through sensors and display on OLED and publish our readings
OLEDrowCounter = 0
msgCounter = 0
OLEDColumn = 0
OLEDrowCounterBase = 0
while True:
    ds18b20_sensor.convert_temp()
    time.sleep_ms(250)
    oled.fill(0)
    for device in sensors:
        s = binascii.hexlify(device)
        readable_string = s.decode('ascii')
        #print(readable_string)
        #print(msgCounter)
        #even msg, so shift to next column
        if (math.fmod(msgCounter, 2) == 0):
            OLEDColumn = 0
        else:
            OLEDColumn = 64
        #Are we on the second row of readings#
        if (msgCounter > 1):
            OLEDrowCounterBase = 36
        OLEDrowCounter = OLEDrowCounterBase
        #print(OLEDrowCounterBase)
        #print only the last 4 digits of the sensor id
        oled.text(readable_string[-4:], OLEDColumn, OLEDrowCounter, 1)
        #print(OLEDrowCounter)
        #print(ds18b20_sensor.read_temp(device))
        OLEDrowCounter += 12
        if (secrets.SCALE  == "F"):
            #convert from Celcius and round the value
            tempF = round((ds18b20_sensor.read_temp(device) * 1.8)+32,1)
        else:
            #leave as C and round
            tempF = round(ds18b20_sensor.read_temp(device),1)
        
        #add any offset needed
        tempF += float(mysensors.OFFSETS[readable_string])
        #display our sensor reading
        oled.text(str(tempF) + " " + secrets.SCALE,OLEDColumn,OLEDrowCounter,1)
        #print(OLEDrowCounter)
           
        #publish our readings to MQTT for HA
        #get the localtime
        year, month, day, hour, mins, secs, weekday, yearday = time.localtime()

        #publish our reading to MQTT
        pub = b'homeassistant/sensor/' + readable_string + b'/state'
        #print our timestamped msg
        print("{:02d}-{:02d}-{}T{:02d}:{:02d}:{:02d}".format(year, month, day, hour, mins, secs), pub +"="+ str(tempF))
        
        state = b'{"Time":"' + "{:02d}-{:02d}-{}T{:02d}:{:02d}:{:02d}".format(year, month, day, hour, mins, secs) + b'","temperature":"' + str(tempF) + b'"}'
        client.publish(pub, state)  #no retain
        
        #only fit 2 in a row
        if (math.fmod(msgCounter, 2) == 0):
            OLEDrowCounter += 12
        msgCounter += 1
        
        OLEDrowCounter = OLEDrowCounterBase
        #pet the dog
        wdt.feed()
        
    oled.show()
    OLEDrowCounter = 0 #reset counter
    #print(OLEDrowCounter)

    msgCounter = 0
    OLEDrowCounterBase = 0
    
    #sleep for 10 seconds
    time.sleep(5)
    #pet the dog
    wdt.feed()
    time.sleep(5)
                                  