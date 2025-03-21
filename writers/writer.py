import os
import time
import csv
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class TrafficWriter:
    """网络流量记录器"""
    
    def __init__(self, path: str, format: str, interval_type: str):
        """
        初始化记录器
        
        Args:
            path: 保存路径
            format: 文件格式 (csv, txt, log)
            interval_type: 文件分割间隔 (week, day, hour)
        """
        self.path = path
        self.format = format
        self.interval_type = interval_type
        self.current_file = None
        
        os.makedirs(self.path, exist_ok=True)

    def _get_filename(self) -> str:
        """根据间隔类型生成文件名"""
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

    def write(self, packets: List[Dict]) -> None:
        """将数据包写入文件"""
        if not packets:
            return
        
        filename = self._get_filename()
        
        if self.format == "csv":
            self._write_csv(filename, packets)
        elif self.format == "txt":
            self._write_txt(filename, packets)
        else:  # log
            self._write_log(filename, packets)

    def _write_csv(self, filename: str, packets: List[Dict]) -> None:
        headers = ['timestamp', 'src_ip', 'dest_ip', 'src_port', 'dest_port', 'src_mac', 'dest_mac']
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
                        f"MAC {packet['src_mac']} -> {packet['dest_mac']}\n")
        logger.info(f"Wrote {len(packets)} packets to {filename}")

    def _write_log(self, filename: str, packets: List[Dict]) -> None:
        with open(filename, 'a') as f:
            for packet in packets:
                f.write(f"[{packet['timestamp']}] INFO - Traffic: {packet['src_ip']}:{packet['src_port']} -> "
                        f"{packet['dest_ip']}:{packet['dest_port']} "
                        f"MAC {packet['src_mac']} -> {packet['dest_mac']}\n")
        logger.info(f"Wrote {len(packets)} packets to {filename}")