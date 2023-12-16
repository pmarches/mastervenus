# What is this?

mastervenus is software interacts with devices on mastervolt's masterbus. That bus is a canbus at 250Kbps. 

Devices that have been tested with this software are:
- DC Shunt
- Mass combi


# Ways to connect a masterbus to GX

1. Use the VEBus connection
A OctoGX has a VEBus that operates at the same speed (250Kbps) than masterbus. I used  with a home made adataper, however the VEBus connector is not electrically isolated. 

2. Dedicated CAN to ethernet gateway device
A better way is to have a dedicated ECAN to Ethernet gateway device. Then configure mastervenus to communicate with this gateway device. This provides electrical isolation and allows devices to communicate over IP instead of the masterbus wiring.

# Green Mastervolt cable pinout


| Pin number | Description | Color          |
|------------|-------------|----------------|
| 1          | CAN High    | Red and White  |
| 2          | CAN Low     | Red            |
| 3          | Ground      | Green          |
| 4          | +12V        | Blue           |
| 5          | +12V        | Blue and White |
| 6          | Ground      | Green          |
| 7          | NC          | Brown          |
| 8          | NC          | Brown and white|


# CANBus configuration

Masterbus is based on standard canbus. The bus speed is 250000. 

```
sudo ip link set down can1
sudo ip link set can1 type can bitrate 250000 restart-ms 100`
sudo ip link set up can1`
sudo ip -details -statistics link show can1
```


# Protocol overview 

The protocol is inspired by a request/response scheme. When a masterview device starts up, it broadcasts a message that requires connected devices to tell the masterview what attributes they offer. Then, the masterview will send a request to each networked device to request the value of a particular attribute. The value is transmitted in clear, as a IEEE734 float. For more details, see the lua wireshark dissector.


## CAN Packet format

Values are sent over the wire encoded as floats. Labels for units such as "A" for Amps, "V" for volts, etc.. are also sent over the wire. Packet length is determined by the canId and attribute type. 

## Devices

The DCShunt is the device supplying power power to the bus. The masterview starts talking on the bus later because it needs time to boot up.


## Masterview display device
Device Id is 0x0194 or 0x840a

This device will query for other devices to announce themselves upon startup. It will then start querying regularly for certain field values from selected devices. The fields selected reflect what is required to be displayed on the screen.

# How can I use the wireshark dissector?
----
You can start wireshark with the following flags to enable the masterbus dissector. The sample capture files will work with this dissector. However, the packet format is not of the canbus format. In canbus, nothing is byte aligned and I do not want to spend the work doing it.

`wireshark -Xlua_script:masterbusDissector.lua`

# How can I capture my own wireshark capture file?
---
`tcpdump -i can1 -w ~/my_capture_file.pcap`

How can I decode more messages?
---
Please modify the wireshark dissector first. It is better to add information in the dissector, you can iterate faster. Also, other projects might find it a usefull starting point.
