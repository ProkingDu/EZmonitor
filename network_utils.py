from scapy.all import get_if_list
import sys
import ipaddress

def is_private_ip(ip):
    """检查 IP 是否为内网地址"""
    private_networks = [
        ipaddress.IPv4Network("10.0.0.0/8"),
        ipaddress.IPv4Network("172.16.0.0/12"),
        ipaddress.IPv4Network("192.168.0.0/16")
    ]
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in network for network in private_networks)
    except ValueError:
        return False

def get_network_interfaces():
    """获取当前系统的网卡列表"""
    try:
        ifaces = get_if_list()
        if not ifaces:
            raise Exception("未找到可用网卡")
        return ifaces
    except Exception as e:
        print(f"获取网卡列表失败: {e}")
        sys.exit(1)