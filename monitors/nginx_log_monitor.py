import os
import re
import threading
import time
import queue
from datetime import datetime
from typing import Dict, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class NginxLogMonitor:
    """Nginx日志监控类，解析日志并生成流量数据"""

    def __init__(self, logs_dir: str, interval: int = 5, logrotate: bool = False,last_log_time: datetime = None):
        self.logs_dir = logs_dir
        self.interval = interval
        self.packet_queue = queue.Queue()
        self.is_running = False
        self.thread = None
        self.logrotate = logrotate
        self.log_files = self._collect_log_files()
        self.last_log_time = last_log_time or datetime.now().astimezone()

    def _collect_log_files(self) -> List[str]:
        """收集Nginx日志文件"""
        log_files = []
        today = datetime.now().strftime("%Y%m%d")
        # if self.logrotate:
        #     pattern = f"*.log-{today}"
        # else:
        #     pattern = "*.log"
        for f in Path(self.logs_dir).glob("*.log"):
            if not f.is_file():
                continue
            file_name = f.name
            if "error" in file_name.lower() or "errlog" in file_name.lower():
                continue
            if not re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\.log$', file_name) and file_name != "global_access.log":
                continue
            log_files.append(str(f))
        logger.info(f"Collected log files from {self.logs_dir}: {log_files}")
        # print(log_files)
        return log_files

    def _parse_nginx_log(self, current_time: datetime):
        """解析Nginx日志，从最后一行向前直到时间超出范围"""
        for log_file in self.log_files:
            if not os.path.exists(log_file):
                continue
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if not lines:
                        continue
                    for line in reversed(lines):
                        line = line.strip()
                        if not line:
                            continue
                        match = re.match(
                            r'(\S+)\|(\S+)\|\[([^]]+)\]\|([^|]+)\|(\d+\s+\d+)\|"([^"]*)"\|\[UA\]([^|]+)\[UA\]\|(\S+)\|(\S+)',
                            line
                        )
                        if match:
                            remote_addr,remote_port, time_local, request, status_bytes, referer, user_agent,ip,port = match.groups()
                            status, body_bytes = status_bytes.split()
                            log_time = datetime.strptime(time_local, '%d/%b/%Y:%H:%M:%S %z')
                            # print(log_time,self.last_log_time,current_time)
                            if log_time > current_time:
                                continue
                            if log_time <= self.last_log_time:
                                break
                            dt = datetime.strptime(time_local, '%d/%b/%Y:%H:%M:%S %z')
                            time_local = dt.strftime("%Y-%m-%d %H:%M:%S")
                            print("捕获到Nginx流量")
                            packet_info = {
                                'timestamp': time_local,
                                'src_ip': remote_addr,
                                # 'dest_ip': ip,
                                "src_port" : remote_port,
                                # "dest_port" : port,
                                # 'src_mac': "N/A",
                                # 'dest_mac': "N/A",
                                'interface': "nginx",
                                'url': request,
                                'user_agent': user_agent,
                            }
                            self.packet_queue.put({"nginx": [packet_info]})
                        else:
                            logger.debug(f"Line in {log_file} did not match expected format: {line[:50]}...")
            except Exception as e:
                logger.error(f"Error reading {log_file}: {e}")

    def _monitor(self):
        logger.info(f"Starting Nginx log monitoring on {self.logs_dir}")
        while self.is_running:
            try:
                current_time = datetime.now().astimezone()
                self._parse_nginx_log(current_time)
                self.last_log_time = current_time
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in Nginx log monitoring: {e}")

    def start(self) -> None:
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._monitor)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Nginx log monitor started")

    def stop(self) -> None:
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            logger.info("Nginx log monitor stopped")

    def get_packet_queue(self) -> queue.Queue:
        return self.packet_queue