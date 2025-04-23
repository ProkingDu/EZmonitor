import os
import time
import csv
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class TrafficWriter:
    """网络流量记录器"""

    def __init__(self, path: str, format: str, interval_type: str, filter_superfluous_ip: bool = False, fake_img: bool = False):
        self.path = path
        self.format = format
        self.interval_type = interval_type
        self.filter_superfluous_ip = filter_superfluous_ip
        self.fake_img = fake_img
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

        return os.path.join(full_path, f"{timestamp}.{self.format}")

    def _merge_packets(self, packets: List[Dict]) -> List[Dict]:
        """仅对网卡流量数据包进行合并，Nginx日志不合并"""
        if not self.filter_superfluous_ip:
            return packets

        if packets and packets[0].get('interface') == 'nginx':
            return packets

        merged = {}
        for packet in packets:
            key = (packet['src_ip'], packet['src_port'], packet['interface'])
            if key in merged:
                merged[key]['timestamp'] = packet['timestamp']
            else:
                merged[key] = packet
        return list(merged.values())

    def _rename_to_original(self, filename: str) -> None:
        """将伪装的图片文件改回原始格式"""
        fake_filename = filename.rsplit('.', 1)[0] + '.jpg'
        if os.path.exists(fake_filename):
            os.rename(fake_filename, filename)
            logger.info(f"已将伪装文件 {fake_filename} 改回 {filename}")

    def _rename_to_fake(self, filename: str) -> None:
        """将日志文件伪装为图片格式"""
        fake_filename = filename.rsplit('.', 1)[0] + '.jpg'
        os.rename(filename, fake_filename)
        logger.info(f"已将日志文件 {filename} 伪装为 {fake_filename}")

    def write(self, packets: List[Dict]) -> None:
        if not packets:
            return

        filtered_packets = self._merge_packets(packets)
        filename = self._get_filename()

        # 写入前将伪装文件改回原始格式
        self._rename_to_original(filename)

        if self.format == "csv":
            self._write_csv(filename, filtered_packets)
        elif self.format == "txt":
            self._write_txt(filename, filtered_packets)
        else:  # log
            self._write_log(filename, filtered_packets)

        # 写入后根据 fake_img 设置伪装
        if self.fake_img:
            self._rename_to_fake(filename)

    def _write_csv(self, filename: str, packets: List[Dict]) -> None:
        headers = ['timestamp', 'src_ip', 'src_port', 'interface', 'url',
                   'user_agent']
        mode = 'a' if os.path.exists(filename) else 'w'
        with open(filename, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if mode == 'w':
                writer.writeheader()
            # print(packets)
            writer.writerows(packets)
        logger.info(f"Wrote {len(packets)} packets to {filename}")

    def _write_txt(self, filename: str, packets: List[Dict]) -> None:
        with open(filename, 'a') as f:
            for packet in packets:
                f.write(f"{packet['timestamp']} {packet['src_ip']}:{packet['src_port']} -> "
                        f"{packet['dest_ip']}:{packet['dest_port']} "
                        f"MAC {packet['src_mac']} -> {packet['dest_mac']} "
                        f"Interface: {packet['interface']} "
                        f"URL: {packet.get('url', 'N/A')} "
                        f"User-Agent: {packet.get('user_agent', 'N/A')}\n")
        logger.info(f"Wrote {len(packets)} packets to {filename}")

    def _write_log(self, filename: str, packets: List[Dict]) -> None:
        with open(filename, 'a') as f:
            for packet in packets:
                f.write(f"[{packet['timestamp']}] INFO - Traffic: {packet['src_ip']}:{packet['src_port']} -> "
                        f"{packet['dest_ip']}:{packet['dest_port']} "
                        f"MAC {packet['src_mac']} -> {packet['dest_mac']} "
                        f"Interface: {packet['interface']} "
                        f"URL: {packet.get('url', 'N/A')} "
                        f"User-Agent: {packet.get('user_agent', 'N/A')}\n")
        logger.info(f"Wrote {len(packets)} packets to {filename}")