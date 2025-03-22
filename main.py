import argparse
import logging
from config_manager import ConfigManager
from monitors.monitor_factory import MonitorFactory
from writers.writer import TrafficWriter
from observers.observer import TrafficObserver
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Network Traffic Monitoring System")
    parser.add_argument('--config', type=str, required=True, help="Path to the config file")
    args = parser.parse_args()

    # 加载配置
    config_manager = ConfigManager(args.config)
    
    # 获取系统配置
    system_config = config_manager.get_system_config()
    filter_internal_ip = system_config['filter_internal_ip']
    filter_superfluous_ip = system_config['filter_superfluous_ip']

    # 创建监视器
    monitors_config = config_manager.get_monitors_config()
    monitors = MonitorFactory.create_monitors_from_config(monitors_config, filter_internal_ip)
    
    # 创建记录器
    writers_config = config_manager.get_writers_config()
    writer = TrafficWriter(
        path=writers_config['path'],
        format=writers_config['format'],
        interval_type=writers_config['interval_type'],
        filter_superfluous_ip=filter_superfluous_ip
    )
    
    # 创建观察器
    observers_config = config_manager.get_observers_config()
    observer = TrafficObserver(
        path=writers_config['path'],
        enabled=observers_config['enabled'],
        cleanup_days=observers_config['cleanup_days']
    )

    try:
        # 启动所有组件
        for monitor in monitors:
            monitor.start()
        observer.start()
        
        # 主循环：定期写入数据
        while True:
            for monitor in monitors:
                packets = monitor.get_packets()
                if packets:
                    writer.write(packets)
                    monitor.clear_packets()
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        for monitor in monitors:
            monitor.stop()
        observer.stop()

if __name__ == "__main__":
    main()