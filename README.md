#What is this?

mastervenus is software interacts with devices on mastervolt's masterbus. That bus is a canbus at 250Kbps. 

Devices that have been tested with this software are:
- DC Shunt
- Mass combi


#Ways to connect a masterbus to GX

1. Use the VEBus connection
A OctoGX has a VEBus that can be connected to masterbus with a home made adataper, however the VEBus connector is not electrically isolated. 

2. Dedicated CAN to ethernet gateway device
A better way is to have a dedicated ECAN to Ethernet gateway device. Then configure mastervenus to communicate with this gateway device. This provides electrical isolation and allows devices to communicate over IP instead of the masterbus wiring.

3. 
