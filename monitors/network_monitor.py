from scapy.all import sniff, get_if_list, get_if_hwaddr
import threading
import time
from typing import List, Dict, Optional, Set
import logging
import ipaddress

logger = logging.getLogger(__name__)

class NetworkMonitor:
    """网络流量监控类"""
    
    def __init__(self, interface: str, interval: int = 5, ports: Optional[Set[int]] = None, filter_internal_ip: bool = False):
        self.interface = interface
        self.interval = interval
        self.ports = ports
        self.filter_internal_ip = filter_internal_ip
        self.is_running = False
        self.thread = None
        self.packets: List[Dict] = []
        self.mac_address = self._get_mac_address()
        
        if interface not in get_if_list():
            raise ValueError(f"Interface {interface} not found. Available interfaces: {get_if_list()}")

    def _get_mac_address(self) -> str:
        try:
            return get_if_hwaddr(self.interface)
        except Exception as e:
            logger.error(f"Failed to get MAC address for {self.interface}: {e}")
            return "00:00:00:00:00:00"

    def _is_internal_ip(self, ip: str) -> bool:
        internal_networks = [
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("127.0.0.0/8")
        ]
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in network for network in internal_networks)

    def _packet_handler(self, packet) -> None:
        try:
            if packet.haslayer('Ether') and packet.haslayer('IP'):
                eth = packet.getlayer('Ether')
                ip = packet.getlayer('IP')
                
                src_port = dest_port = 0
                if packet.haslayer('TCP'):
                    tcp = packet.getlayer('TCP')
                    src_port = tcp.sport
                    dest_port = tcp.dport
                elif packet.haslayer('UDP'):
                    udp = packet.getlayer('UDP')
                    src_port = udp.sport
                    dest_port = udp.dport
                
                if self.ports is not None:
                    if dest_port not in self.ports:
                        return
                
                if self.filter_internal_ip:
                    if self._is_internal_ip(ip.src):
                        return
                
                packet_info = {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(packet.time)),
                    'src_ip': ip.src,
                    'dest_ip': ip.dst,
                    'src_port': src_port,
                    'dest_port': dest_port,
                    'src_mac': eth.src,
                    'dest_mac': eth.dst,
                    'interface': self.interface  # 添加网卡信息
                }
                self.packets.append(packet_info)
                
        except Exception as e:
            logger.error(f"Error processing packet: {e}")

    def _monitor(self) -> None:
        logger.info(f"Starting monitoring on {self.interface} with ports: {self.ports if self.ports else 'all'}")
        while self.is_running:
            try:
                sniff(iface=self.interface, prn=self._packet_handler, store=0, timeout=self.interval)
            except Exception as e:
                logger.error(f"Error in monitoring {self.interface}: {e}")

    def start(self) -> None:
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._monitor)
            self.thread.daemon = True
            self.thread.start()
            logger.info(f"Monitor started on interface: {self.interface}")

    def stop(self) -> None:
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            logger.info(f"Monitor stopped on interface: {self.interface}")

    def get_packets(self) -> List[Dict]:
        return self.packets

    def clear_packets(self) -> None:
        self.packets.clear()