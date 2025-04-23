from monitors.network_monitor import NetworkMonitor
from monitors.nginx_log_monitor import NginxLogMonitor
from typing import List, Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)

class MonitorFactory:
    """工厂类，用于创建监控器实例"""

    @staticmethod
    def create_network_monitor(interface: str, interval: int = 5, ports: Optional[Set[int]] = None,
                              filter_internal_ip: bool = False) -> NetworkMonitor:
        try:
            monitor = NetworkMonitor(interface, interval, ports, filter_internal_ip)
            logger.info(f"Created network monitor for {interface}")
            return monitor
        except ValueError as e:
            logger.error(f"Failed to create network monitor: {e}")
            raise

    @staticmethod
    def create_nginx_log_monitor(logs_dir: str, interval: int = 5,logrotate: bool = False,) -> NginxLogMonitor:
        try:
            monitor = NginxLogMonitor(logs_dir, interval,logrotate)
            logger.info(f"Created Nginx log monitor for {logs_dir}")
            return monitor
        except ValueError as e:
            logger.error(f"Failed to create Nginx log monitor: {e}")
            raise

    @staticmethod
    def create_monitors_from_config(config: Dict, filter_internal_ip: bool = False) -> List:
        monitors = []
        # 创建网卡监控器
        if config.get("monitors", []) is not None:
            for monitor_config in config.get("monitors", []):
                interface = monitor_config["interface"]
                interval = monitor_config.get("interval", 5)
                ports = set(monitor_config.get("ports", [])) if monitor_config.get("ports") else None
                monitor = MonitorFactory.create_network_monitor(interface, interval, ports, filter_internal_ip)
                monitors.append(monitor)
        # 创建Nginx日志监控器
        middleware_config = config.get("middleware", {})
        if middleware_config.get("type") == "nginx":
            logs_dir = middleware_config.get("logs_dir", "/var/log/nginx")
            interval = 5  # 默认值，可在middleware中添加interval字段
            logrotate = middleware_config.get("logrotate", False)
            monitor = MonitorFactory.create_nginx_log_monitor(logs_dir, interval,logrotate)
            monitors.append(monitor)
        return monitors