import argparse
import logging
from config_manager import ConfigManager
from monitors.monitor_factory import MonitorFactory
from writers.writer import TrafficWriter
from observers.observer import TrafficObserver
import time
import queue
from datetime import datetime

logger = logging.getLogger(__name__)

def main():
    try:
        parser = argparse.ArgumentParser(description="Network Traffic Monitoring System")
        parser.add_argument('--config', type=str, required=True, help="Path to the config file")
        args = parser.parse_args()
    except Exception as e:
        print("需要指定配置文件。\r示例：python3 main.py --config config.yaml")
        exit(0)

    # 加载配置
    config_manager = ConfigManager(args.config)

    # 获取系统配置
    system_config = config_manager.get_system_config()
    filter_internal_ip = system_config['filter_internal_ip']
    filter_superfluous_ip = system_config['filter_superfluous_ip']

    # 创建所有监控器（网卡 + Nginx）
    monitors = MonitorFactory.create_monitors_from_config(config_manager.get_config(), filter_internal_ip)

    # 创建记录器
    writers_config = config_manager.get_writers_config()
    writer = TrafficWriter(
        path=writers_config['path'],
        format=writers_config['format'],
        interval_type=writers_config['interval_type'],
        filter_superfluous_ip=filter_superfluous_ip,
        fake_img=writers_config['fake_img']  # 传递 fake_img 参数
    )

    # 创建观察器
    # observers_config = config_manager.get_observers_config()
    # observer = TrafficObserver(
    #     path=writers_config['path'],  # 使用writers的path
    #     enabled=observers_config['enabled'],
    #     cleanup_days=observers_config['cleanup_days']
    # )

    try:
        for monitor in monitors:
            monitor.start()
        # observer.start()

        while True:
            current_time = datetime.now().astimezone()

            for monitor in monitors:
                packet_queue = monitor.get_packet_queue()
                packets_by_interface = {}
                while not packet_queue.empty():
                    try:
                        packet_dict = packet_queue.get_nowait()
                        interface = list(packet_dict.keys())[0]
                        if interface not in packets_by_interface:
                            packets_by_interface[interface] = []
                        packets_by_interface[interface].extend(packet_dict[interface])
                    except queue.Empty:
                        break
                for interface, packets in packets_by_interface.items():
                    if packets:
                        print(f"Writing {len(packets)} packets for interface {interface}")
                        logger.info(f"Writing {len(packets)} packets for interface {interface}")
                        writer.write(packets)
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        for monitor in monitors:
            monitor.stop()
        # observer.stop()

if __name__ == "__main__":
    main()