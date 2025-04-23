from scapy.all import *

packets =sniff(iface="eth0",filter="tcp port 80",count=1)

for packet in packets:
    print(packets[TCP][0][Raw])