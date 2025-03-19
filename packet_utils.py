from scapy.all import IP, TCP, UDP
from datetime import datetime
from network_utils import is_private_ip

def packet_handler(packet, logger, target_ports):
    """处理捕获的数据包，只记录外部 IP 和指定端口的入网流量"""
    if IP in packet and (TCP in packet or UDP in packet):
        # 获取源 IP
        src_ip = packet[IP].src
        
        # 只记录外部 IP
        if not is_private_ip(src_ip):
            # 获取协议类型和端口
            if TCP in packet:
                protocol = "TCP"
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
            else:  # UDP
                protocol = "UDP"
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
            
            # 只记录目标端口在指定列表中的流量
            if dst_port in target_ports:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                src_mac = packet.src
                
                # 使用元组作为键，包含所有关键字段
                key = (current_time, src_ip, src_port, dst_port, src_mac, protocol)
                if key not in logger.traffic_records:
                    logger.traffic_records[key]["first_time"] = current_time
                logger.traffic_records[key]["count"] += 1