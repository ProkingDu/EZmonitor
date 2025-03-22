from monitors.network_monitor import NetworkMonitor
from typing import List, Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)

class MonitorFactory:
    """工厂类，用于创建NetworkMonitor实例"""
    
    @staticmethod
    def create_monitor(interface: str, interval: int = 5, ports: Optional[Set[int]] = None, filter_internal_ip: bool = False) -> NetworkMonitor:
        try:
            monitor = NetworkMonitor(interface, interval, ports, filter_internal_ip)
            logger.info(f"Created monitor for {interface} with interval {interval}s and ports {ports if ports else 'all'}")
            return monitor
        except ValueError as e:
            logger.error(f"Failed to create monitor: {e}")
            raise

    @staticmethod
    def create_monitors_from_config(config: List[Dict], filter_internal_ip: bool = False) -> List[NetworkMonitor]:
        monitors = []
        for monitor_config in config:
            interface = monitor_config["interface"]
            interval = monitor_config.get("interval", 5)
            ports = set(monitor_config.get("ports", [])) if monitor_config.get("ports") else None
            monitor = MonitorFactory.create_monitor(interface, interval, ports, filter_internal_ip)
            monitors.append(monitor)
        return monitors