from scapy.all import sniff
import threading
import argparse
import sys
import os
from traffic_logger import TrafficLogger
from packet_utils import packet_handler
from network_utils import *

# 全局变量
sniffing = True
target_ports = []

def start_sniffing(interface, log_dir):
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
                  timeout=5)  # 每 60 秒写入一次
            logger.save_to_csv()
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        logger.save_to_csv()  # 退出时保存剩余记录
        sniffing = False

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="网络流量监控程序（仅记录外部 IP 和指定端口，折叠重复记录）")
    parser.add_argument("--log-dir", type=str, default=os.getcwd(), help="日志保存的根目录")
    parser.add_argument("--ports", type=int, nargs="+", required=True, help="要监控的端口号（多个端口用空格分隔）")
    args = parser.parse_args()

    # 设置目标端口
    global target_ports
    target_ports = args.ports
    for port in target_ports:
        if not (0 <= port <= 65535):
            print(f"错误：端口号 {port} 无效，必须在 0-65535 之间")
            sys.exit(1)

    # 获取网卡列表
    interfaces = get_network_interfaces()
    print("可用网卡列表：")
    for i, iface in enumerate(interfaces):
        print(f"{i}: {iface}")
    print("-1: 监控所有网卡")

    # 用户选择网卡
    while True:
        try:
            choice = int(input("请选择网卡索引（-1 表示所有网卡）: "))
            if choice == -1:
                selected_interface = None
                break
            elif 0 <= choice < len(interfaces):
                selected_interface = interfaces[choice]
                break
            else:
                print("无效的索引，请重新选择")
        except ValueError:
            print("请输入有效的数字")

    # 创建嗅探线程
    sniff_thread = threading.Thread(
        target=start_sniffing,
        args=(selected_interface, args.log_dir)
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