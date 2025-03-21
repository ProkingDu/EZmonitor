from monitor_factory import MonitorFactory
from network_monitor import NetworkMonitor
from scapy.all import get_if_list
import time
import logging

logger = logging.getLogger(__name__)

def test_single_monitor():
    """测试单个监控实例"""
    interfaces = get_if_list()
    if not interfaces:
        logger.error("No network interfaces available")
        return
    
    factory = MonitorFactory()
    try:
        # 测试特定端口监控
        monitor = factory.create_monitor(
            interface=interfaces[0],
            interval=5,
            ports={80, 443}
        )
        monitor.start()
        time.sleep(5)  # 运行5秒
        monitor.stop()
        
        packets = monitor.get_packets()
        print(f"\nTest Single Monitor - {interfaces[0]}:")
        print(f"Captured {len(packets)} packets")
        for packet in packets[:5]:
            print(packet)
            
        # 验证端口过滤
        for packet in packets:
            assert packet['src_port'] in {80, 443} or packet['dest_port'] in {80, 443}, \
                "Port filtering failed"
        print("Port filtering test passed")
        
    except Exception as e:
        logger.error(f"Test single monitor failed: {e}")

def test_multiple_monitors():
    """测试多个监控实例"""
    interfaces = get_if_list()
    if not interfaces:
        logger.error("No network interfaces available")
        return
    
    factory = MonitorFactory()
    monitors = []
    
    try:
        # 配置多个监控
        config = {
            "monitors": [
                {"interface": interfaces[0], "interval": 5, "ports": [22, 23]},
                {"interface": interfaces[1] if len(interfaces) > 1 else interfaces[0], "interval": 5}
            ]
        }
        monitors = factory.create_monitors_from_config(config)
        
        # 启动所有监控
        for monitor in monitors:
            monitor.start()
        
        time.sleep(5)  # 运行5秒
        
        # 停止并验证结果
        for monitor in monitors:
            monitor.stop()
            packets = monitor.get_packets()
            print(f"\nTest Multiple Monitors - {monitor.interface}:")
            print(f"Captured {len(packets)} packets")
            for packet in packets[:5]:
                print(packet)
            
            # 如果指定了端口，验证端口过滤
            if monitor.ports:
                for packet in packets:
                    assert packet['src_port'] in monitor.ports or packet['dest_port'] in monitor.ports, \
                        "Port filtering failed in multiple monitors"
        
        print("Multiple monitors test passed")
        
    except Exception as e:
        logger.error(f"Test multiple monitors failed: {e}")
    finally:
        for monitor in monitors:
            monitor.stop()

if __name__ == "__main__":
    print(f"Available interfaces: {get_if_list()}")
    
    # 运行测试
    print("\nRunning single monitor test...")
    test_single_monitor()
    
    # print("\nRunning multiple monitors test...")
    # test_multiple_monitors()