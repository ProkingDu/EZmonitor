import os
import time
import csv
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class TrafficWriter:
    """网络流量记录器"""
    
    def __init__(self, path: str, format: str, interval_type: str, filter_superfluous_ip: bool = False):
        self.path = path
        self.format = format
        self.interval_type = interval_type
        self.filter_superfluous_ip = filter_superfluous_ip
        self.current_file = None
        os.makedirs(self.path, exist_ok=True)

    def _get_filename(self) -> str:
        now = time.localtime()
        month_dir = time.strftime("%Y-%m", now)
        full_path = os.path.join(self.path, month_dir)
        os.makedirs(full_path, exist_ok=True)
        
        if self.interval_type == "week":
            timestamp = time.strftime("%Y%m%d", now) + f"_week{time.localtime().tm_yday // 7}"
        elif self.interval_type == "hour":
            timestamp = time.strftime("%Y%m%d_%H", now)
        else:  # day
            timestamp = time.strftime("%Y%m%d", now)
        
        return os.path.join(full_path, f"traffic_{timestamp}.{self.format}")

    def _merge_packets(self, packets: List[Dict]) -> List[Dict]:
        if not self.filter_superfluous_ip:
            return packets
        
        merged = {}
        for packet in packets:
            key = (packet['src_ip'], packet['dest_ip'], packet['src_port'], packet['dest_port'],
                   packet['src_mac'], packet['dest_mac'], packet['interface'])  # 添加 interface 到 key
            if key in merged:
                merged[key]['timestamp'] = packet['timestamp']
            else:
                merged[key] = packet
        
        return list(merged.values())

    def write(self, packets: List[Dict]) -> None:
        if not packets:
            return
        
        filtered_packets = self._merge_packets(packets)
        filename = self._get_filename()
        
        if self.format == "csv":
            self._write_csv(filename, filtered_packets)
        elif self.format == "txt":
            self._write_txt(filename, filtered_packets)
        else:  # log
            self._write_log(filename, filtered_packets)

    def _write_csv(self, filename: str, packets: List[Dict]) -> None:
        headers = ['timestamp', 'src_ip', 'dest_ip', 'src_port', 'dest_port', 'src_mac', 'dest_mac', 'interface']
        mode = 'a' if os.path.exists(filename) else 'w'
        with open(filename, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if mode == 'w':
                writer.writeheader()
            writer.writerows(packets)
        logger.info(f"Wrote {len(packets)} packets to {filename}")

    def _write_txt(self, filename: str, packets: List[Dict]) -> None:
        with open(filename, 'a') as f:
            for packet in packets:
                f.write(f"{packet['timestamp']} {packet['src_ip']}:{packet['src_port']} -> "
                        f"{packet['dest_ip']}:{packet['dest_port']} "
                        f"MAC {packet['src_mac']} -> {packet['dest_mac']} "
                        f"Interface: {packet['interface']}\n")
        logger.info(f"Wrote {len(packets)} packets to {filename}")

    def _write_log(self, filename: str, packets: List[Dict]) -> None:
        with open(filename, 'a') as f:
            for packet in packets:
                f.write(f"[{packet['timestamp']}] INFO - Traffic: {packet['src_ip']}:{packet['src_port']} -> "
                        f"{packet['dest_ip']}:{packet['dest_port']} "
                        f"MAC {packet['src_mac']} -> {packet['dest_mac']} "
                        f"Interface: {packet['interface']}\n")
        logger.info(f"Wrote {len(packets)} packets to {filename}")