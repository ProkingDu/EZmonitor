import os
import time
import threading
import logging
from typing import List

logger = logging.getLogger(__name__)

class TrafficObserver:
    """网络流量文件观察器，用于定时清理"""
    
    def __init__(self, path: str, enabled: bool, cleanup_days: int, check_interval: int = 3600):
        """
        初始化观察器
        
        Args:
            path: 文件保存路径
            enabled: 是否启用清理
            cleanup_days: 清理多少天前的文件
            check_interval: 检查间隔（秒）
        """
        self.path = path
        self.enabled = enabled
        self.cleanup_days = cleanup_days
        self.check_interval = check_interval
        self.is_running = False
        self.thread = None

    def _cleanup(self) -> None:
        """清理过期文件"""
        now = time.time()
        cutoff = now - (self.cleanup_days * 86400)
        
        for root, _, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < cutoff:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed expired file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to remove {file_path}: {e}")

    def _observe(self) -> None:
        """观察线程循环"""
        logger.info(f"Observer started with cleanup_days: {self.cleanup_days}")
        while self.is_running:
            if self.enabled:
                self._cleanup()
            time.sleep(self.check_interval)

    def start(self) -> None:
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._observe)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Observer started")

    def stop(self) -> None:
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            logger.info("Observer stopped")