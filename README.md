# Temp-Sensor
Micropython Code to control Raspberry Pi Pico w for multiple temperature sensors and OLED display.

This project sends to an MQTT broker and sends autodiscovery info for <a href="https://www.home-assistant.io/" target="_new">Homeassistant</a>.

I will update this with more details as time goes on.

Why?  Well I installed an outdoor wood boiler from <a href="https://heatmasterss.com/" target="_new">HeatMasterSS</a> and I wanted to monitor various temperatures on my boiler pipes.
I tried a 4 probe BBQ thermometer and it was unreliable and way too expensive.  I built this for about $30 CAD.  The BBQ one was over $100 and didn't do what I wanted.
So here it is, mostly as a backup for myself, but if anyone else can find value, fill your boots!

I also figured out a way to read from the Seimens Logo8 controller to monitor directly, but its not yet ready to publish.

Uses: <BR>
Stainless Steel Probe DS18B20<BR>
OLED Display Module, 128 x 64 0.96 inches OLED Display 12864 LCD Module for 51 Series MSP430 STM32<BR>
Pico W

Instructions:

Uses Tools->Manage Packages->Micropython-umqtt.simple

<BR>
Circuit Visuals<BR>
<img src="/images/front.png"><BR><BR>
<img src="/images/back.png"><BR>
<img src="/images/HA.png"><BR>
