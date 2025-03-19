import os
import sys
import threading
from scapy.all import sniff
from traffic_logger import TrafficLogger
from packet_utils import packet_handler
from network_utils import get_network_interfaces
from config_manager import Config
import traceback  # 添加导入语句

sniffing = True

def start_sniffing(interface, log_dir, interval, target_ports):
    """开始嗅探指定端口的入网流量并定期记录到 CSV"""
    global sniffing
    logger = TrafficLogger(log_dir)
    try:
        print(f"开始监控 {interface or '所有网卡'} 上端口 {target_ports} 的入网流量（仅外部 IP，折叠重复记录）...")
        print(f"日志保存至: {logger.get_log_path()}")
        print("按 Ctrl+C 停止监控")
        
        # 设置过滤规则，只捕获指定端口的流量
        filter_rule = " or ".join(f"dst port {port}" for port in target_ports)
        while sniffing:
            sniff(iface=interface, 
                  filter=filter_rule,
                  prn=lambda pkt: packet_handler(pkt, logger, target_ports),
                  store=0,
                  timeout=interval)  # 每 interval 秒写入一次
            logger.save_to_csv()
    except Exception as e:
        print("发生错误:")
        traceback.print_exc()  # 打印详细的错误信息
    finally:
        logger.save_to_csv()  # 退出时保存剩余记录
        sniffing = False

def main():
    # 从命令行读取配置文件路径
    config_path = 'config.yaml'
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        
    # 初始化配置管理器
    config = Config(config_path)
    # 设置目标端口
    global target_ports
    target_ports = config.get('ports')
    for port in target_ports:
        if not (0 <= port <= 65535):
            print(f"错误：端口号 {port} 无效，必须在 0-65535 之间")
            sys.exit(1)

    # 设置接口
    selected_interface = config.get('interface')
    if selected_interface != -1:
        interfaces = get_network_interfaces()
        if selected_interface >= len(interfaces):
            print(f"错误：接口索引 {selected_interface} 无效")
            sys.exit(1)
        selected_interface = interfaces[selected_interface]

    # 创建嗅探线程
    sniff_thread = threading.Thread(
        target=start_sniffing,
        args=(selected_interface, config.get('log_dir'), config.get('interval'), target_ports)
    )
    
    # 启动嗅探线程
    sniff_thread.start()
    
    try:
        # 主线程等待用户中断
        while sniff_thread.is_alive():
            sniff_thread.join(1)
    except KeyboardInterrupt:
        print("\n正在停止监控...")
        global sniffing
        sniffing = False
        sniff_thread.join()

if __name__ == "__main__":
    if os.name == 'posix' and os.geteuid() != 0:
        print("此程序需要 root 权限运行，请使用 sudo 执行")
        sys.exit(1)
    elif os.name == 'nt':
        print("此程序在 Windows 下需要管理员权限运行")
        sys.exit(1)
    else:
        main()