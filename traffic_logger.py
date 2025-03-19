import os
import csv
from datetime import datetime
from collections import defaultdict

class TrafficLogger:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.traffic_records = defaultdict(lambda: {"count": 0, "first_time": None})

    def get_log_path(self):
        current_year_month = datetime.now().strftime("%Y-%m")
        log_subdir = os.path.join(self.log_dir, current_year_month)
        os.makedirs(log_subdir, exist_ok=True)
        return os.path.join(log_subdir, f"traffic_{datetime.now().strftime('%Y%m%d')}.csv")

    def save_to_csv(self):
        log_file = self.get_log_path()
        with open(log_file, 'a', newline='') as f:
            csv_writer = csv.writer(f)
            if os.path.getsize(log_file) == 0:
                csv_writer.writerow(["Time", "Source_IP", "Source_Port", "Dest_Port", "Source_MAC", "Protocol", "Request_Count"])
            for key, data in self.traffic_records.items():
                time, src_ip, src_port, dst_port, src_mac, protocol = key
                csv_writer.writerow([data["first_time"], src_ip, src_port, dst_port, src_mac, protocol, data["count"]])
            self.traffic_records.clear()  # 清空记录，准备下次写入
    
    def save_to_log(self):
        log_file = self.get_log_path().replace('.csv', '.log')
        with open(log_file, 'a') as f:
            for key, data in self.traffic_records.items():
                time, src_ip, src_port, dst_port, src_mac, protocol = key
                log_entry = f"{data['first_time']} - Source_IP: {src_ip}, Source_Port: {src_port}, Dest_Port: {dst_port}, Source_MAC: {src_mac}, Protocol: {protocol}, Request_Count: {data['count']}\n"
                f.write(log_entry)
        self.traffic_records.clear()  # 清空记录，准备下次写入
